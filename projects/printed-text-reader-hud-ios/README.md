# Printed Text Reader HUD — iPhone app

I read printed questions with your camera and work out the answer — right on your phone. Point the camera at a quiz question, and I read the question whole plus its printed A–D choices, pick the answer, and highlight it green on the camera with a one-line reason. No scrolling, no typing.

This is the native iPhone version of my web prototype. The web version reads with Tesseract in a browser, and that is the part that kept failing on photographed screens — garbled words, shifted boxes, missing choices. This app uses Apple's Vision framework instead, which reads photographed screens far better and gives me the exact position of every word, so the boxes land where the text actually is.

## What I do

- **Camera-first solving.** Live camera with a green scan frame. I read each question whole plus its printed choices, pick the answer, and highlight it green on the camera with a reason and an answer banner.
- **Maths, computed — never guessed.** Arithmetic (+ − × ÷), fractions, number words ("twelve divided by three"), "subtract 3 from 10", half/quarter of, and story problems (sharing equally, packing into groups, profit, speed, change from a bill). A worked answer that matches no printed choice is re-analysed against the choices instead of force-fit.
- **Multiple choice from my built-in bank.** About 90 general-knowledge questions and 230 cybersecurity questions (Security+ and CISSP domains), plus a Wikipedia lookup when a question is not in the bank. "NOT" questions pick the choice the reference does *not* back.
- **I match by the answer text, never the letter.** If the quiz shuffles Ho-Oh from C to B, my answer follows it to B.
- **Fill-in repair.** If the read comes back garbled ("Whig ib the rote Mhcramon…"), I swap the unrecognised words for the closest ones I know and show the filled-in question on the card ("FILLED IN AS: …"). A clean read is never rewritten.
- **Suggested answers.** When I cannot confirm an answer, I offer my best guess instead of nothing — amber chip on the camera banner and an amber dashed box on the suggested choice, tagged "SUGGESTED ANSWER — BEST GUESS, NOT CONFIRMED". A guess can never be mistaken for a confirmed green answer.
- **Tap to focus.** Turn it on, tap the question on the camera to read only a band around your tap (enlarged), then tap the middle of the choices to read only those. Works with a finger or a mouse. If a choices tap finds fewer than three choices, I retry it in black-and-white on my own.
- **Teach me.** Each card shows what I detected. Select lines in the "TEXT IT READ" box and mark them as the question or as the choices A–D, and I re-solve from your correction. Tap "Teach this answer" and I remember that answer for the question from now on — by its text, so shuffles still work.
- **Photo.** A screenshot of a quiz reads far cleaner than a photo of a screen. Use the Photo button to read one from your library.
- **Multi-question frames** split into one card per question.
- **Dark screens.** I detect a dark-mode quiz screen, invert it, and read the inverted copy if it reads better.
- **Burst frames.** Every scan grabs up to 3 frames and keeps the sharpest read; if the read was shaky, I say so.

Everything reads on this phone. The camera image is never uploaded. Maths never leaves the phone — only a general-knowledge question I cannot solve on-device goes to Wikipedia, and only the question text goes, never the image.

I am a prototype, not a full AI. My cybersecurity bank is study knowledge only — it is not a claim that I hold CISSP. I hold CompTIA Security+.

## How to open it in Xcode and run it on your iPhone

You need your MacBook Pro with Xcode installed (free from the App Store). No accounts, keys, or extra tools.

1. **Get the project onto your Mac.** Copy the whole `printed-text-reader-hud-ios` folder to your Mac (AirDrop, USB, or iCloud Drive — whichever you like).
2. **Open it.** Double-click `PrintedTextReaderHUD.xcodeproj`. Xcode opens with the project.
3. **Pick your team (one time).** In the left sidebar, click the top item, `PrintedTextReaderHUD` (the blue project icon). In the middle pane, make sure the `PrintedTextReaderHUD` target is selected, then click the **Signing & Capabilities** tab. Tick **Automatically manage signing**, then pick your Apple ID under **Team**. If your Apple ID is not there, click **Add Account…** and sign in with it. (A free Apple ID works for running it on your own iPhone.)
4. **Plug in your iPhone.** Connect it with a cable. Unlock it and tap **Trust** if it asks.
5. **Pick your iPhone as the run destination.** At the top of the Xcode window, next to the ▶ Run button, click the device menu (it may say "My Mac" or a simulator name) and choose your iPhone.
6. **Run it.** Click ▶ (or press ⌘R). The first time, your iPhone may ask you to trust the developer: go to **Settings → General → VPN & Device Management** on the iPhone, tap your Apple ID, and tap **Trust**.
7. **Use it.** Point the camera at a printed question and tap **Scan & solve**. Allow the camera when it asks.

That is all. There is nothing to install, no API key, and no server.

## How to use it

- **Scan & solve** — the main button. Hold the phone steady, fill the frame with the question and its choices, tap it.
- **Tap to focus** — turn it on first, then tap the question on the camera, then tap the middle of the choices. Tapping the camera without the toggle on does nothing — the toggle is what arms it.
- **Auto-scan** — scans again every couple of seconds while it is on.
- **Photo** — read a screenshot or a photo from your library. A screenshot reads cleanest.
- **Correcting a misread** — the text I read is in the "TEXT IT READ" box at the bottom. Fix a word or a digit there and tap **Re-solve from this text**. Or select lines in that box and tap **Mark selection as the question** or **Mark selection as choices A–D**.
- **Teaching an answer** — on any card, tap **Teach this answer**. I remember it for that question, matched by its text, so a shuffled retake still finds it.

## What was checked, and what was not

The solver — the part that works out answers — was tested on this machine against 40 checks, and all 40 pass: every one of James's confirmed quiz answers (12×6 → C·72, 1/4+1/4 → D·1/2, the runner, the candles, 782÷23, the theatre, the Pokémon questions, "Honest Abe" → D·Abraham Lincoln, residual risk → Senior management), the shuffle cases (Ho-Oh under B, Charizard under A), the fill-in repair (including the exact garbled read from his screenshot), and the Wikipedia fallback with a stubbed reference.

What was **not** checked here, and only you can check: the app has never run on a real iPhone yet. The camera, the live Vision read, the tap-to-focus reading, and the real Wikipedia call cannot be exercised from this machine — the Swift toolchain here is Linux, and UIKit, AVFoundation, and Vision do not exist on it. The iOS files were syntax-checked as far as this environment allows, but **the real test is opening the project in Xcode on your Mac and running it on your iPhone**. If Xcode reports an error on the first build, send me the exact message and I will fix it.

## Files

```
PrintedTextReaderHUD.xcodeproj/     the Xcode project (open this)
PrintedTextReaderHUD/
  PrintedTextReaderHUDApp.swift    app entry point
  Info.plist                       camera + photo permissions
  Assets.xcassets/                 app icon + accent colour
  Solver/                          the answer engine (pure Swift, tested)
    TextUtils.swift                normalising, numbers, regex, edit distance
    MathEngine.swift               safe maths parser, word maths, story problems
    TextSegmentation.swift         splitting frames into questions + choices
    FactBank.swift                 90 general + 232 cybersecurity facts
    FactSolver.swift               fact bank, definitions, vocabulary
    WikiLookup.swift               Wikipedia reference lookup + dictionary
    FillInRepair.swift             fill-in-the-blank repair for garbled reads
    Solver.swift                   the dispatch: maths → facts → vocabulary → web
  Vision/
    TextRecognizer.swift           Apple's Vision reader (on-device)
    RecognizedText.swift           lines + boxes + the desk-paper column filter
  Camera/
    CameraManager.swift            AVFoundation capture + burst frames
    CameraPreviewView.swift        live preview + overlay boxes + taps
  UI/
    ContentView.swift              main screen + scan flow + teach mode
    QuestionCardView.swift         one card per question
    SelectableTextView.swift       the read-text box with selection
PrintedTextReaderHUDTests/
  SolverTests.swift                the same ground-truth cases, as XCTest
```

## Pushed to GitHub — Nov 20, 2026

James asked me to push this to the portfolio repository on Nov 20, 2026. That push overrides the hold-off for this upload only — future updates still wait until he says they are working.

## If something goes wrong

- **Xcode says "Signing requires a development team"** — step 3 above. Pick your Apple ID under Team.
- **"Untrusted Developer" on the iPhone** — Settings → General → VPN & Device Management → tap your Apple ID → Trust.
- **The camera shows nothing** — check the app has camera permission (Settings → Text Reader HUD → Camera). The first run asks; if you tapped "Don't Allow", turn it on there.
- **A scan reads garbage** — use the Photo button with a screenshot instead of photographing the screen, or turn on Tap to focus and tap the question, then the choices. If a word is misread, fix it in the "TEXT IT READ" box and re-solve.
- **The answer is wrong** — check the "FILLED IN AS" line and the text box: if a number or a word was misread, fix it and re-solve, or tap "Teach this answer" once you know the right one.
