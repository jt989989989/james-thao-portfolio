// WikiLookup.swift
// My reference lookup: when a question with choices cannot be solved
// on the phone, I ask Wikipedia (free, no key) and score each printed
// choice against what it finds. The question decides the search; the
// options are never sent as the answer — they are only scored against
// what the reference says. "NOT" questions pick the choice the
// reference does NOT back. Maths never leaves the phone — this lookup
// is only reached for questions the maths engine did not claim.
//
// Answers from here are labelled "ANSWER FROM A WEB LOOKUP"; answers
// worked out on the phone are labelled "WORKED OUT ON THIS PHONE".

import Foundation

#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// Given a search query, fetch encyclopedia text about it. The app
/// passes the real Wikipedia fetcher; tests pass a stub.
public typealias WikiFetcher = (String) async -> String?

/// Given a word, fetch its dictionary entry. Nil means "no entry".
public typealias DictionaryFetcher = (String) async -> WordInfo?

// MARK: - Wikipedia (real network, iOS)

/// Fetch up to 16,000 characters of Wikipedia text for a query: search
/// first, then the extracts of the top pages.
public func fetchWikiCorpus(_ query: String) async -> String? {
    guard let searchURL = URL(string: "https://en.wikipedia.org/w/api.php?action=query&list=search&srnamespace=0&srlimit=4&format=json&origin=*&srsearch=" + query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!) else {
        return nil
    }
    guard let searchData = await fetchData(searchURL, timeout: 7) else { return nil }
    guard let searchJSON = try? JSONSerialization.jsonObject(with: searchData) as? [String: Any],
          let queryObj = searchJSON["query"] as? [String: Any],
          let results = queryObj["search"] as? [[String: Any]], !results.isEmpty else { return nil }
    let snippets = results.compactMap { $0["snippet"] as? String }.map { stripHtml($0) }.joined(separator: " ")
    let titles = results.compactMap { $0["title"] as? String }.joined(separator: "|")
    guard let pageURL = URL(string: "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&format=json&origin=*&titles=" + titles.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!) else {
        return snippets.isEmpty ? nil : snippets
    }
    if let pageData = await fetchData(pageURL, timeout: 7),
       let pageJSON = try? JSONSerialization.jsonObject(with: pageData) as? [String: Any],
       let q2 = pageJSON["query"] as? [String: Any],
       let pages = q2["pages"] as? [String: Any] {
        let extracts = pages.values.compactMap { ($0 as? [String: Any])?["extract"] as? String }
        let corpus = (snippets + " " + extracts.joined(separator: " "))
        return String(corpus.prefix(16000))
    }
    return snippets.isEmpty ? nil : snippets
}

/// Strip HTML tags and entities from a Wikipedia snippet.
public func stripHtml(_ s: String) -> String {
    var out = regexReplace(#"<[^>]*>"#, in: s, with: " ")
    out = out.replacingOccurrences(of: "&amp;", with: "&")
        .replacingOccurrences(of: "&quot;", with: "\"")
        .replacingOccurrences(of: "&#039;", with: "'")
        .replacingOccurrences(of: "&lt;", with: "<")
        .replacingOccurrences(of: "&gt;", with: ">")
    return out
}

private func fetchData(_ url: URL, timeout: TimeInterval) async -> Data? {
    await withCheckedContinuation { cont in
        var request = URLRequest(url: url, timeoutInterval: timeout)
        request.setValue("PrintedTextReaderHUD/1.0 (personal study prototype)", forHTTPHeaderField: "User-Agent")
        URLSession.shared.dataTask(with: request) { data, response, _ in
            if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                cont.resume(returning: data)
            } else {
                cont.resume(returning: nil)
            }
        }.resume()
    }
}

// MARK: - Scoring

/// Score one printed option against normalised reference text: a big
/// bonus for the whole phrase appearing, then per-word mentions. A
/// purely numeric option scores only on an exact stand-alone match.
public func scoreOptionInCorpus(_ optText: String, _ corpusNorm: String) -> Int {
    let o = normText(optText)
    guard !o.isEmpty else { return 0 }
    var score = 0
    if (" " + corpusNorm + " ").contains(" " + o + " ") { score += 14 }
    var toks = o.split(separator: " ").map(String.init).filter { $0.count > 2 && !solverStopWords.contains($0) }
    if toks.isEmpty { toks = o.split(separator: " ").map(String.init) }
    for w in toks {
        var count = 0
        var searchFrom = corpusNorm.startIndex
        while count < 5, let r = corpusNorm.range(of: w, range: searchFrom..<corpusNorm.endIndex) {
            count += 1
            searchFrom = r.upperBound
        }
        score += min(count, 4)
    }
    if regexContains(#"^\d+$"#, in: o) {
        score = (" " + corpusNorm + " ").contains(" " + o + " ") ? score : 0
    }
    return score
}

/// Is this a "NOT" / "EXCEPT" question — one where the right answer is
/// the choice the reference does NOT back?
public func isNotQuestion(_ stem: String) -> Bool {
    let n = " " + normText(stem) + " "
    return n.contains(" not ") || n.contains(" except ") || n.contains(" not a ") || n.contains(" least likely ")
}

/// Solve a multiple-choice question from the reference lookup.
public func solveMcWiki(_ stem: String, _ opts: [ChoiceOption], fetcher: WikiFetcher) async -> SolveResult? {
    let query = stem.split(separator: " ").joined(separator: " ").trimmingCharacters(in: .whitespaces)
    guard query.count >= 8, let corpus = await fetcher(query), !corpus.isEmpty else { return nil }
    let cn = normText(corpus)
    let scored = opts.map { o in (o, scoreOptionInCorpus(o.text, cn)) }.sorted { $0.1 > $1.1 }
    guard let top = scored.first else { return nil }
    let second = scored.count > 1 ? scored[1] : nil
    if isNotQuestion(stem) {
        // The reference backs the wrong answers — pick the choice it
        // does NOT back, but only when the backing is clear.
        let lowest = scored.last!
        if top.1 >= 6 && top.1 - lowest.1 >= 3 {
            return SolveResult(status: .solved, letter: lowest.0.letter, answerText: lowest.0.text,
                               headline: lowest.0.text,
                               detail: "The reference backs the other options for this question, but not \"\(lowest.0.text)\" — and this is a NOT question, so the odd one out is the answer.",
                               flag: nil, suggested: false, source: .webLookup, maybeLetters: [],
                               sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
        }
        return nil
    }
    if top.1 >= 6 && top.1 - (second?.1 ?? 0) >= 3 {
        return SolveResult(status: .solved, letter: top.0.letter, answerText: top.0.text,
                           headline: top.0.text,
                           detail: "Best match in the reference for this question — \"\(top.0.text)\" is the option the reference supports.",
                           flag: nil, suggested: false, source: .webLookup, maybeLetters: [],
                           sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
    }
    if top.1 >= 6, let second = second {
        return SolveResult(status: .uncertain, letter: nil, answerText: nil,
                           headline: "Not certain between \(top.0.letter) and \(second.0.letter)",
                           detail: "The reference mentions both options for this question, so no single answer stands out.",
                           flag: "⚠ Two options could fit — flagged instead of guessed. Check the exact wording on the page.",
                           suggested: false, source: .webLookup, maybeLetters: [top.0.letter, second.0.letter],
                           sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
    }
    return nil
}

/// An open question with no options: take the reference's first
/// substantial sentence as the answer.
public func solveOpenWiki(_ text: String, fetcher: WikiFetcher) async -> SolveResult? {
    let query = text.split(separator: " ").joined(separator: " ").trimmingCharacters(in: .whitespaces)
    guard query.count >= 8, let corpus = await fetcher(query), !corpus.isEmpty else { return nil }
    let clean = corpus.split(separator: " ").joined(separator: " ").trimmingCharacters(in: .whitespaces)
    let sentences = allMatches(#"[^.!?]+[.!?]+"#, in: clean).map { $0[0] }.filter { $0.trimmingCharacters(in: .whitespaces).count > 25 }
    let sentence = sentences.first ?? String(clean.prefix(180))
    guard !sentence.isEmpty else { return nil }
    return SolveResult(status: .solved, letter: nil, answerText: nil,
                       headline: "Reference answer", detail: oneLine(sentence),
                       flag: nil, suggested: false, source: .webLookup, maybeLetters: [],
                       sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
}

private func oneLine(_ def: String) -> String {
    var d = def.split(separator: " ").joined(separator: " ").trimmingCharacters(in: .whitespaces)
    if let cut = d.range(of: ". ") {
        let pos = d.distance(from: d.startIndex, to: cut.lowerBound)
        if pos > 20 && pos < 150 { d = String(d.prefix(pos + 1)) }
    }
    if d.count > 150 { d = String(d.prefix(147)).trimmingCharacters(in: .whitespaces) + "…" }
    return d
}

// MARK: - Free dictionary (for vocabulary questions)

/// Fetch a word from the free dictionary API. Returns nil on any
/// failure — the built-in dictionary is the offline fallback.
public func fetchDictionaryWord(_ word: String) async -> WordInfo? {
    guard let url = URL(string: "https://api.dictionaryapi.dev/api/v2/entries/en/" + word.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!) else {
        return nil
    }
    guard let data = await fetchData(url, timeout: 7),
          let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
          let entry = json.first,
          let meanings = entry["meanings"] as? [[String: Any]],
          let meaning = meanings.first,
          let defs = meaning["definitions"] as? [[String: Any]],
          let def = defs.first,
          let definition = def["definition"] as? String else { return nil }
    let synonyms = ((def["synonyms"] as? [String]) ?? []) + ((meaning["synonyms"] as? [String]) ?? [])
    return WordInfo(word: entry["word"] as? String ?? word,
                    pos: meaning["partOfSpeech"] as? String ?? "",
                    definition: oneLine(definition), synonyms: synonyms)
}
