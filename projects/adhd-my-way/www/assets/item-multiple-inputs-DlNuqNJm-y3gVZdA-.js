import"./index-B8hAYvA-.js";/*!
 * (C) Ionic http://ionicframework.com - MIT License
 */const l=(n,o,a=["item-multiple-inputs"])=>{const t=n.closest("ion-item");if(!t||typeof MutationObserver>"u")return;const s=()=>a.map(e=>t.classList.contains(e)).join(",");let r=s();const i=new MutationObserver(()=>{const e=s();e!==r&&(r=e,o())});return i.observe(t,{attributes:!0,attributeFilter:["class"]}),i};export{l as c};
