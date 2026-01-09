var sn=Object.defineProperty;var an=(s,t,e)=>t in s?sn(s,t,{enumerable:!0,configurable:!0,writable:!0,value:e}):s[t]=e;var _=(s,t,e)=>an(s,typeof t!="symbol"?t+"":t,e);import{a as pt}from"./apiService.js";(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const i of document.querySelectorAll('link[rel="modulepreload"]'))a(i);new MutationObserver(i=>{for(const n of i)if(n.type==="childList")for(const r of n.addedNodes)r.tagName==="LINK"&&r.rel==="modulepreload"&&a(r)}).observe(document,{childList:!0,subtree:!0});function e(i){const n={};return i.integrity&&(n.integrity=i.integrity),i.referrerPolicy&&(n.referrerPolicy=i.referrerPolicy),i.crossOrigin==="use-credentials"?n.credentials="include":i.crossOrigin==="anonymous"?n.credentials="omit":n.credentials="same-origin",n}function a(i){if(i.ep)return;i.ep=!0;const n=e(i);fetch(i.href,n)}})();/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z2=(s,t,e=[])=>{const a=document.createElementNS("http://www.w3.org/2000/svg",s);return Object.keys(t).forEach(i=>{a.setAttribute(i,String(t[i]))}),e.length&&e.forEach(i=>{const n=Z2(...i);a.appendChild(n)}),a};var nn=([s,t,e])=>Z2(s,t,e);/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const on=s=>Array.from(s.attributes).reduce((t,e)=>(t[e.name]=e.value,t),{}),rn=s=>typeof s=="string"?s:!s||!s.class?"":s.class&&typeof s.class=="string"?s.class.split(" "):s.class&&Array.isArray(s.class)?s.class:"",hn=s=>s.flatMap(rn).map(e=>e.trim()).filter(Boolean).filter((e,a,i)=>i.indexOf(e)===a).join(" "),cn=s=>s.replace(/(\w)(\w*)(_|-|\s*)/g,(t,e,a)=>e.toUpperCase()+a.toLowerCase()),Cs=(s,{nameAttr:t,icons:e,attrs:a})=>{var f;const i=s.getAttribute(t);if(i==null)return;const n=cn(i),r=e[n];if(!r)return console.warn(`${s.outerHTML} icon name was not found in the provided icons object.`);const h=on(s),[c,l,d]=r,p={...l,"data-lucide":i,...a,...h},g=hn(["lucide",`lucide-${i}`,h,a]);g&&Object.assign(p,{class:g});const u=nn([c,p,d]);return(f=s.parentNode)==null?void 0:f.replaceChild(u,s)};/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ln=["svg",o,[["circle",{cx:"16",cy:"4",r:"1"}],["path",{d:"m18 19 1-7-6 1"}],["path",{d:"m5 8 3-3 5.5 3-2.36 3.5"}],["path",{d:"M4.24 14.5a5 5 0 0 0 6.88 6"}],["path",{d:"M13.76 17.5a5 5 0 0 0-6.88-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dn=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M17 12h-2l-2 5-2-10-2 5H7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pn=["svg",o,[["path",{d:"M22 12h-4l-3 9L9 3l-3 9H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gn=["svg",o,[["path",{d:"M6 12H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"}],["path",{d:"M6 8h12"}],["path",{d:"M18.3 17.7a2.5 2.5 0 0 1-3.16 3.83 2.53 2.53 0 0 1-1.14-2V12"}],["path",{d:"M6.6 15.6A2 2 0 1 0 10 17v-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const un=["svg",o,[["path",{d:"M5 17H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-1"}],["polygon",{points:"12 15 17 21 7 21 12 15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ss=["svg",o,[["circle",{cx:"12",cy:"13",r:"8"}],["path",{d:"M5 3 2 6"}],["path",{d:"m22 6-3-3"}],["path",{d:"M6.38 18.7 4 21"}],["path",{d:"M17.64 18.67 20 21"}],["path",{d:"m9 13 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fn=["svg",o,[["path",{d:"M6.87 6.87a8 8 0 1 0 11.26 11.26"}],["path",{d:"M19.9 14.25a8 8 0 0 0-9.15-9.15"}],["path",{d:"m22 6-3-3"}],["path",{d:"M6.26 18.67 4 21"}],["path",{d:"m2 2 20 20"}],["path",{d:"M4 4 2 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vn=["svg",o,[["circle",{cx:"12",cy:"13",r:"8"}],["path",{d:"M12 9v4l2 2"}],["path",{d:"M5 3 2 6"}],["path",{d:"m22 6-3-3"}],["path",{d:"M6.38 18.7 4 21"}],["path",{d:"M17.64 18.67 20 21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xn=["svg",o,[["circle",{cx:"12",cy:"13",r:"8"}],["path",{d:"M5 3 2 6"}],["path",{d:"m22 6-3-3"}],["path",{d:"M6.38 18.7 4 21"}],["path",{d:"M17.64 18.67 20 21"}],["path",{d:"M9 13h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mn=["svg",o,[["circle",{cx:"12",cy:"13",r:"8"}],["path",{d:"M5 3 2 6"}],["path",{d:"m22 6-3-3"}],["path",{d:"M6.38 18.7 4 21"}],["path",{d:"M17.64 18.67 20 21"}],["path",{d:"M12 10v6"}],["path",{d:"M9 13h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mn=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["polyline",{points:"11 3 11 11 14 8 17 11 17 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yn=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bn=["svg",o,[["polygon",{points:"7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wn=["svg",o,[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _n=["svg",o,[["path",{d:"M2 12h20"}],["path",{d:"M10 16v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4"}],["path",{d:"M10 8V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v4"}],["path",{d:"M20 16v1a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2v-1"}],["path",{d:"M14 8V7c0-1.1.9-2 2-2h2a2 2 0 0 1 2 2v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kn=["svg",o,[["path",{d:"M12 2v20"}],["path",{d:"M8 10H4a2 2 0 0 1-2-2V6c0-1.1.9-2 2-2h4"}],["path",{d:"M16 10h4a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-4"}],["path",{d:"M8 20H7a2 2 0 0 1-2-2v-2c0-1.1.9-2 2-2h1"}],["path",{d:"M16 14h1a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cn=["svg",o,[["line",{x1:"21",x2:"3",y1:"6",y2:"6"}],["line",{x1:"17",x2:"7",y1:"12",y2:"12"}],["line",{x1:"19",x2:"5",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sn=["svg",o,[["rect",{width:"6",height:"16",x:"4",y:"2",rx:"2"}],["rect",{width:"6",height:"9",x:"14",y:"9",rx:"2"}],["path",{d:"M22 22H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ln=["svg",o,[["rect",{width:"16",height:"6",x:"2",y:"4",rx:"2"}],["rect",{width:"9",height:"6",x:"9",y:"14",rx:"2"}],["path",{d:"M22 22V2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const An=["svg",o,[["rect",{width:"6",height:"14",x:"4",y:"5",rx:"2"}],["rect",{width:"6",height:"10",x:"14",y:"7",rx:"2"}],["path",{d:"M17 22v-5"}],["path",{d:"M17 7V2"}],["path",{d:"M7 22v-3"}],["path",{d:"M7 5V2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hn=["svg",o,[["rect",{width:"6",height:"14",x:"4",y:"5",rx:"2"}],["rect",{width:"6",height:"10",x:"14",y:"7",rx:"2"}],["path",{d:"M10 2v20"}],["path",{d:"M20 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vn=["svg",o,[["rect",{width:"6",height:"14",x:"4",y:"5",rx:"2"}],["rect",{width:"6",height:"10",x:"14",y:"7",rx:"2"}],["path",{d:"M4 2v20"}],["path",{d:"M14 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pn=["svg",o,[["rect",{width:"6",height:"14",x:"2",y:"5",rx:"2"}],["rect",{width:"6",height:"10",x:"16",y:"7",rx:"2"}],["path",{d:"M12 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dn=["svg",o,[["rect",{width:"6",height:"14",x:"2",y:"5",rx:"2"}],["rect",{width:"6",height:"10",x:"12",y:"7",rx:"2"}],["path",{d:"M22 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fn=["svg",o,[["rect",{width:"6",height:"14",x:"6",y:"5",rx:"2"}],["rect",{width:"6",height:"10",x:"16",y:"7",rx:"2"}],["path",{d:"M2 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tn=["svg",o,[["rect",{width:"6",height:"10",x:"9",y:"7",rx:"2"}],["path",{d:"M4 22V2"}],["path",{d:"M20 22V2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bn=["svg",o,[["rect",{width:"6",height:"14",x:"3",y:"5",rx:"2"}],["rect",{width:"6",height:"10",x:"15",y:"7",rx:"2"}],["path",{d:"M3 2v20"}],["path",{d:"M21 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const On=["svg",o,[["line",{x1:"3",x2:"21",y1:"6",y2:"6"}],["line",{x1:"3",x2:"21",y1:"12",y2:"12"}],["line",{x1:"3",x2:"21",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const En=["svg",o,[["line",{x1:"21",x2:"3",y1:"6",y2:"6"}],["line",{x1:"15",x2:"3",y1:"12",y2:"12"}],["line",{x1:"17",x2:"3",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rn=["svg",o,[["line",{x1:"21",x2:"3",y1:"6",y2:"6"}],["line",{x1:"21",x2:"9",y1:"12",y2:"12"}],["line",{x1:"21",x2:"7",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zn=["svg",o,[["rect",{width:"6",height:"16",x:"4",y:"6",rx:"2"}],["rect",{width:"6",height:"9",x:"14",y:"6",rx:"2"}],["path",{d:"M22 2H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const In=["svg",o,[["rect",{width:"9",height:"6",x:"6",y:"14",rx:"2"}],["rect",{width:"16",height:"6",x:"6",y:"4",rx:"2"}],["path",{d:"M2 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $n=["svg",o,[["rect",{width:"14",height:"6",x:"5",y:"14",rx:"2"}],["rect",{width:"10",height:"6",x:"7",y:"4",rx:"2"}],["path",{d:"M22 7h-5"}],["path",{d:"M7 7H1"}],["path",{d:"M22 17h-3"}],["path",{d:"M5 17H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zn=["svg",o,[["rect",{width:"14",height:"6",x:"5",y:"14",rx:"2"}],["rect",{width:"10",height:"6",x:"7",y:"4",rx:"2"}],["path",{d:"M2 20h20"}],["path",{d:"M2 10h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wn=["svg",o,[["rect",{width:"14",height:"6",x:"5",y:"14",rx:"2"}],["rect",{width:"10",height:"6",x:"7",y:"4",rx:"2"}],["path",{d:"M2 14h20"}],["path",{d:"M2 4h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nn=["svg",o,[["rect",{width:"14",height:"6",x:"5",y:"16",rx:"2"}],["rect",{width:"10",height:"6",x:"7",y:"2",rx:"2"}],["path",{d:"M2 12h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jn=["svg",o,[["rect",{width:"14",height:"6",x:"5",y:"12",rx:"2"}],["rect",{width:"10",height:"6",x:"7",y:"2",rx:"2"}],["path",{d:"M2 22h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Un=["svg",o,[["rect",{width:"14",height:"6",x:"5",y:"16",rx:"2"}],["rect",{width:"10",height:"6",x:"7",y:"6",rx:"2"}],["path",{d:"M2 2h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qn=["svg",o,[["rect",{width:"10",height:"6",x:"7",y:"9",rx:"2"}],["path",{d:"M22 20H2"}],["path",{d:"M22 4H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gn=["svg",o,[["rect",{width:"14",height:"6",x:"5",y:"15",rx:"2"}],["rect",{width:"10",height:"6",x:"7",y:"3",rx:"2"}],["path",{d:"M2 21h20"}],["path",{d:"M2 3h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xn=["svg",o,[["path",{d:"M17.5 12c0 4.4-3.6 8-8 8A4.5 4.5 0 0 1 5 15.5c0-6 8-4 8-8.5a3 3 0 1 0-6 0c0 3 2.5 8.5 12 13"}],["path",{d:"M16 12h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yn=["svg",o,[["path",{d:"M10 17c-5-3-7-7-7-9a2 2 0 0 1 4 0c0 2.5-5 2.5-5 6 0 1.7 1.3 3 3 3 2.8 0 5-2.2 5-5"}],["path",{d:"M22 17c-5-3-7-7-7-9a2 2 0 0 1 4 0c0 2.5-5 2.5-5 6 0 1.7 1.3 3 3 3 2.8 0 5-2.2 5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kn=["svg",o,[["circle",{cx:"12",cy:"5",r:"3"}],["line",{x1:"12",x2:"12",y1:"22",y2:"8"}],["path",{d:"M5 12H2a10 10 0 0 0 20 0h-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jn=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M16 16s-1.5-2-4-2-4 2-4 2"}],["path",{d:"M7.5 8 10 9"}],["path",{d:"m14 9 2.5-1"}],["path",{d:"M9 10h0"}],["path",{d:"M15 10h0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qn=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M8 15h8"}],["path",{d:"M8 9h2"}],["path",{d:"M14 9h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const to=["svg",o,[["path",{d:"M2 12 7 2"}],["path",{d:"m7 12 5-10"}],["path",{d:"m12 12 5-10"}],["path",{d:"m17 12 5-10"}],["path",{d:"M4.5 7h15"}],["path",{d:"M12 16v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const eo=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"14.31",x2:"20.05",y1:"8",y2:"17.94"}],["line",{x1:"9.69",x2:"21.17",y1:"8",y2:"8"}],["line",{x1:"7.38",x2:"13.12",y1:"12",y2:"2.06"}],["line",{x1:"9.69",x2:"3.95",y1:"16",y2:"6.06"}],["line",{x1:"14.31",x2:"2.83",y1:"16",y2:"16"}],["line",{x1:"16.62",x2:"10.88",y1:"12",y2:"21.94"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const so=["svg",o,[["rect",{x:"2",y:"4",width:"20",height:"16",rx:"2"}],["path",{d:"M10 4v4"}],["path",{d:"M2 8h20"}],["path",{d:"M6 4v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ao=["svg",o,[["path",{d:"M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"}],["path",{d:"M10 2c1 .5 2 2 2 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const io=["svg",o,[["rect",{width:"20",height:"5",x:"2",y:"3",rx:"1"}],["path",{d:"M4 8v11a2 2 0 0 0 2 2h2"}],["path",{d:"M20 8v11a2 2 0 0 1-2 2h-2"}],["path",{d:"m9 15 3-3 3 3"}],["path",{d:"M12 12v9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const no=["svg",o,[["rect",{width:"20",height:"5",x:"2",y:"3",rx:"1"}],["path",{d:"M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"}],["path",{d:"m9.5 17 5-5"}],["path",{d:"m9.5 12 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const oo=["svg",o,[["rect",{width:"20",height:"5",x:"2",y:"3",rx:"1"}],["path",{d:"M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"}],["path",{d:"M10 12h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ro=["svg",o,[["path",{d:"M3 3v18h18"}],["path",{d:"M7 12v5h12V8l-5 5-4-4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ho=["svg",o,[["path",{d:"M19 9V6a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v3"}],["path",{d:"M3 16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H7v-2a2 2 0 0 0-4 0Z"}],["path",{d:"M5 18v2"}],["path",{d:"M19 18v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const co=["svg",o,[["path",{d:"M15 5H9"}],["path",{d:"M15 9v3h4l-7 7-7-7h4V9h6z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lo=["svg",o,[["path",{d:"M15 6v6h4l-7 7-7-7h4V6h6z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const po=["svg",o,[["path",{d:"M19 15V9"}],["path",{d:"M15 15h-3v4l-7-7 7-7v4h3v6z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const go=["svg",o,[["path",{d:"M18 15h-6v4l-7-7 7-7v4h6v6z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uo=["svg",o,[["path",{d:"M5 9v6"}],["path",{d:"M9 9h3V5l7 7-7 7v-4H9V9z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fo=["svg",o,[["path",{d:"M6 9h6V5l7 7-7 7v-4H6V9z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vo=["svg",o,[["path",{d:"M9 19h6"}],["path",{d:"M9 15v-3H5l7-7 7 7h-4v3H9z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xo=["svg",o,[["path",{d:"M9 18v-6H5l7-7 7 7h-4v6H9z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mo=["svg",o,[["path",{d:"m3 16 4 4 4-4"}],["path",{d:"M7 20V4"}],["rect",{x:"15",y:"4",width:"4",height:"6",ry:"2"}],["path",{d:"M17 20v-6h-2"}],["path",{d:"M15 20h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mo=["svg",o,[["path",{d:"m3 16 4 4 4-4"}],["path",{d:"M7 20V4"}],["path",{d:"M17 10V4h-2"}],["path",{d:"M15 10h4"}],["rect",{x:"15",y:"14",width:"4",height:"6",ry:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ls=["svg",o,[["path",{d:"m3 16 4 4 4-4"}],["path",{d:"M7 20V4"}],["path",{d:"M20 8h-5"}],["path",{d:"M15 10V6.5a2.5 2.5 0 0 1 5 0V10"}],["path",{d:"M15 14h5l-5 6h5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yo=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 8v8"}],["path",{d:"m8 12 4 4 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bo=["svg",o,[["path",{d:"M19 3H5"}],["path",{d:"M12 21V7"}],["path",{d:"m6 15 6 6 6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wo=["svg",o,[["path",{d:"M2 12a10 10 0 1 1 10 10"}],["path",{d:"m2 22 10-10"}],["path",{d:"M8 22H2v-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _o=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m16 8-8 8"}],["path",{d:"M16 16H8V8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ko=["svg",o,[["path",{d:"M17 7 7 17"}],["path",{d:"M17 17H7V7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Co=["svg",o,[["path",{d:"m3 16 4 4 4-4"}],["path",{d:"M7 20V4"}],["path",{d:"M11 4h4"}],["path",{d:"M11 8h7"}],["path",{d:"M11 12h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const So=["svg",o,[["path",{d:"M12 22a10 10 0 1 1 10-10"}],["path",{d:"M22 22 12 12"}],["path",{d:"M22 16v6h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lo=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m8 8 8 8"}],["path",{d:"M16 8v8H8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ao=["svg",o,[["path",{d:"m7 7 10 10"}],["path",{d:"M17 7v10H7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ho=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M12 8v8"}],["path",{d:"m8 12 4 4 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vo=["svg",o,[["path",{d:"M12 2v14"}],["path",{d:"m19 9-7 7-7-7"}],["circle",{cx:"12",cy:"21",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Po=["svg",o,[["path",{d:"M12 17V3"}],["path",{d:"m6 11 6 6 6-6"}],["path",{d:"M19 21H5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Do=["svg",o,[["path",{d:"m3 16 4 4 4-4"}],["path",{d:"M7 20V4"}],["path",{d:"m21 8-4-4-4 4"}],["path",{d:"M17 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const As=["svg",o,[["path",{d:"m3 16 4 4 4-4"}],["path",{d:"M7 20V4"}],["path",{d:"M11 4h10"}],["path",{d:"M11 8h7"}],["path",{d:"M11 12h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hs=["svg",o,[["path",{d:"m3 16 4 4 4-4"}],["path",{d:"M7 4v16"}],["path",{d:"M15 4h5l-5 6h5"}],["path",{d:"M15 20v-3.5a2.5 2.5 0 0 1 5 0V20"}],["path",{d:"M20 18h-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fo=["svg",o,[["path",{d:"M12 5v14"}],["path",{d:"m19 12-7 7-7-7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const To=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M16 12H8"}],["path",{d:"m12 8-4 4 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bo=["svg",o,[["path",{d:"m9 6-6 6 6 6"}],["path",{d:"M3 12h14"}],["path",{d:"M21 19V5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Oo=["svg",o,[["path",{d:"M8 3 4 7l4 4"}],["path",{d:"M4 7h16"}],["path",{d:"m16 21 4-4-4-4"}],["path",{d:"M20 17H4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Eo=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m12 8-4 4 4 4"}],["path",{d:"M16 12H8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ro=["svg",o,[["path",{d:"M3 19V5"}],["path",{d:"m13 6-6 6 6 6"}],["path",{d:"M7 12h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zo=["svg",o,[["path",{d:"m12 19-7-7 7-7"}],["path",{d:"M19 12H5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Io=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M8 12h8"}],["path",{d:"m12 16 4-4-4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $o=["svg",o,[["path",{d:"M3 5v14"}],["path",{d:"M21 12H7"}],["path",{d:"m15 18 6-6-6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zo=["svg",o,[["path",{d:"m16 3 4 4-4 4"}],["path",{d:"M20 7H4"}],["path",{d:"m8 21-4-4 4-4"}],["path",{d:"M4 17h16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wo=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M8 12h8"}],["path",{d:"m12 16 4-4-4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const No=["svg",o,[["path",{d:"M17 12H3"}],["path",{d:"m11 18 6-6-6-6"}],["path",{d:"M21 5v14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jo=["svg",o,[["path",{d:"M5 12h14"}],["path",{d:"m12 5 7 7-7 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uo=["svg",o,[["path",{d:"m3 8 4-4 4 4"}],["path",{d:"M7 4v16"}],["rect",{x:"15",y:"4",width:"4",height:"6",ry:"2"}],["path",{d:"M17 20v-6h-2"}],["path",{d:"M15 20h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qo=["svg",o,[["path",{d:"m3 8 4-4 4 4"}],["path",{d:"M7 4v16"}],["path",{d:"M17 10V4h-2"}],["path",{d:"M15 10h4"}],["rect",{x:"15",y:"14",width:"4",height:"6",ry:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vs=["svg",o,[["path",{d:"m3 8 4-4 4 4"}],["path",{d:"M7 4v16"}],["path",{d:"M20 8h-5"}],["path",{d:"M15 10V6.5a2.5 2.5 0 0 1 5 0V10"}],["path",{d:"M15 14h5l-5 6h5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Go=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m16 12-4-4-4 4"}],["path",{d:"M12 16V8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xo=["svg",o,[["path",{d:"m21 16-4 4-4-4"}],["path",{d:"M17 20V4"}],["path",{d:"m3 8 4-4 4 4"}],["path",{d:"M7 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yo=["svg",o,[["path",{d:"m5 9 7-7 7 7"}],["path",{d:"M12 16V2"}],["circle",{cx:"12",cy:"21",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ko=["svg",o,[["path",{d:"m18 9-6-6-6 6"}],["path",{d:"M12 3v14"}],["path",{d:"M5 21h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jo=["svg",o,[["path",{d:"M2 8V2h6"}],["path",{d:"m2 2 10 10"}],["path",{d:"M12 2A10 10 0 1 1 2 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qo=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M8 16V8h8"}],["path",{d:"M16 16 8 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tr=["svg",o,[["path",{d:"M7 17V7h10"}],["path",{d:"M17 17 7 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ps=["svg",o,[["path",{d:"m3 8 4-4 4 4"}],["path",{d:"M7 4v16"}],["path",{d:"M11 12h4"}],["path",{d:"M11 16h7"}],["path",{d:"M11 20h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const er=["svg",o,[["path",{d:"M22 12A10 10 0 1 1 12 2"}],["path",{d:"M22 2 12 12"}],["path",{d:"M16 2h6v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sr=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M8 8h8v8"}],["path",{d:"m8 16 8-8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ar=["svg",o,[["path",{d:"M7 7h10v10"}],["path",{d:"M7 17 17 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ir=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m16 12-4-4-4 4"}],["path",{d:"M12 16V8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nr=["svg",o,[["path",{d:"M5 3h14"}],["path",{d:"m18 13-6-6-6 6"}],["path",{d:"M12 7v14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const or=["svg",o,[["path",{d:"m3 8 4-4 4 4"}],["path",{d:"M7 4v16"}],["path",{d:"M11 12h10"}],["path",{d:"M11 16h7"}],["path",{d:"M11 20h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ds=["svg",o,[["path",{d:"m3 8 4-4 4 4"}],["path",{d:"M7 4v16"}],["path",{d:"M15 4h5l-5 6h5"}],["path",{d:"M15 20v-3.5a2.5 2.5 0 0 1 5 0V20"}],["path",{d:"M20 18h-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rr=["svg",o,[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hr=["svg",o,[["path",{d:"m4 6 3-3 3 3"}],["path",{d:"M7 17V3"}],["path",{d:"m14 6 3-3 3 3"}],["path",{d:"M17 17V3"}],["path",{d:"M4 21h16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cr=["svg",o,[["path",{d:"M12 6v12"}],["path",{d:"M17.196 9 6.804 15"}],["path",{d:"m6.804 9 10.392 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lr=["svg",o,[["circle",{cx:"12",cy:"12",r:"4"}],["path",{d:"M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dr=["svg",o,[["circle",{cx:"12",cy:"12",r:"1"}],["path",{d:"M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5Z"}],["path",{d:"M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pr=["svg",o,[["path",{d:"M2 10v3"}],["path",{d:"M6 6v11"}],["path",{d:"M10 3v18"}],["path",{d:"M14 8v7"}],["path",{d:"M18 5v13"}],["path",{d:"M22 10v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gr=["svg",o,[["path",{d:"M2 13a2 2 0 0 0 2-2V7a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0V4a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0v-4a2 2 0 0 1 2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ur=["svg",o,[["circle",{cx:"12",cy:"8",r:"6"}],["path",{d:"M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fr=["svg",o,[["path",{d:"m14 12-8.5 8.5a2.12 2.12 0 1 1-3-3L11 9"}],["path",{d:"M15 13 9 7l4-4 6 6h3a8 8 0 0 1-7 7z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fs=["svg",o,[["path",{d:"M4 4v16h16"}],["path",{d:"m4 20 7-7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vr=["svg",o,[["path",{d:"M9 12h.01"}],["path",{d:"M15 12h.01"}],["path",{d:"M10 16c.5.3 1.2.5 2 .5s1.5-.2 2-.5"}],["path",{d:"M19 6.3a9 9 0 0 1 1.8 3.9 2 2 0 0 1 0 3.6 9 9 0 0 1-17.6 0 2 2 0 0 1 0-3.6A9 9 0 0 1 12 3c2 0 3.5 1.1 3.5 2.5s-.9 2.5-2 2.5c-.8 0-1.5-.4-1.5-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xr=["svg",o,[["path",{d:"M4 10a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"}],["path",{d:"M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"}],["path",{d:"M8 21v-5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v5"}],["path",{d:"M8 10h8"}],["path",{d:"M8 18h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M12 7v10"}],["path",{d:"M15.4 10a4 4 0 1 0 0 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ts=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"m9 12 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"}],["path",{d:"M12 18V6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const br=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M7 12h5"}],["path",{d:"M15 9.4a4 4 0 1 0 0 5.2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["line",{x1:"12",x2:"12.01",y1:"17",y2:"17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _r=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M8 8h8"}],["path",{d:"M8 12h8"}],["path",{d:"m13 17-5-1h1a4 4 0 0 0 0-8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["line",{x1:"12",x2:"12",y1:"16",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"8",y2:"8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"m9 8 3 3v7"}],["path",{d:"m12 11 3-3"}],["path",{d:"M9 12h6"}],["path",{d:"M9 16h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["line",{x1:"8",x2:"16",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"m15 9-6 6"}],["path",{d:"M9 9h.01"}],["path",{d:"M15 15h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ar=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["line",{x1:"12",x2:"12",y1:"8",y2:"16"}],["line",{x1:"8",x2:"16",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M8 12h4"}],["path",{d:"M10 16V9.5a2.5 2.5 0 0 1 5 0"}],["path",{d:"M8 16h7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M9 16h5"}],["path",{d:"M9 12h5a2 2 0 1 0 0-4h-3v9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["path",{d:"M11 17V8h4"}],["path",{d:"M11 12h3"}],["path",{d:"M9 16h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}],["line",{x1:"15",x2:"9",y1:"9",y2:"15"}],["line",{x1:"9",x2:"15",y1:"9",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fr=["svg",o,[["path",{d:"M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tr=["svg",o,[["path",{d:"M22 18H6a2 2 0 0 1-2-2V7a2 2 0 0 0-2-2"}],["path",{d:"M17 14V4a2 2 0 0 0-2-2h-1a2 2 0 0 0-2 2v10"}],["rect",{width:"13",height:"8",x:"8",y:"6",rx:"1"}],["circle",{cx:"18",cy:"20",r:"2"}],["circle",{cx:"9",cy:"20",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Br=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m4.9 4.9 14.2 14.2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Or=["svg",o,[["path",{d:"M4 13c3.5-2 8-2 10 2a5.5 5.5 0 0 1 8 5"}],["path",{d:"M5.15 17.89c5.52-1.52 8.65-6.89 7-12C11.55 4 11.5 2 13 2c3.22 0 5 5.5 5 8 0 6.5-4.2 12-10.49 12C5.11 22 2 22 2 20c0-1.5 1.14-1.55 3.15-2.11Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Er=["svg",o,[["rect",{width:"20",height:"12",x:"2",y:"6",rx:"2"}],["circle",{cx:"12",cy:"12",r:"2"}],["path",{d:"M6 12h.01M18 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rr=["svg",o,[["line",{x1:"18",x2:"18",y1:"20",y2:"10"}],["line",{x1:"12",x2:"12",y1:"20",y2:"4"}],["line",{x1:"6",x2:"6",y1:"20",y2:"14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zr=["svg",o,[["path",{d:"M3 3v18h18"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ir=["svg",o,[["path",{d:"M3 3v18h18"}],["path",{d:"M13 17V9"}],["path",{d:"M18 17V5"}],["path",{d:"M8 17v-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $r=["svg",o,[["path",{d:"M3 3v18h18"}],["rect",{width:"4",height:"7",x:"7",y:"10",rx:"1"}],["rect",{width:"4",height:"12",x:"15",y:"5",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zr=["svg",o,[["path",{d:"M3 3v18h18"}],["rect",{width:"12",height:"4",x:"7",y:"5",rx:"1"}],["rect",{width:"7",height:"4",x:"7",y:"13",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wr=["svg",o,[["path",{d:"M3 3v18h18"}],["path",{d:"M7 16h8"}],["path",{d:"M7 11h12"}],["path",{d:"M7 6h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nr=["svg",o,[["line",{x1:"12",x2:"12",y1:"20",y2:"10"}],["line",{x1:"18",x2:"18",y1:"20",y2:"4"}],["line",{x1:"6",x2:"6",y1:"20",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jr=["svg",o,[["path",{d:"M3 5v14"}],["path",{d:"M8 5v14"}],["path",{d:"M12 5v14"}],["path",{d:"M17 5v14"}],["path",{d:"M21 5v14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ur=["svg",o,[["path",{d:"M4 20h16"}],["path",{d:"m6 16 6-12 6 12"}],["path",{d:"M8 12h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qr=["svg",o,[["path",{d:"M9 6 6.5 3.5a1.5 1.5 0 0 0-1-.5C4.683 3 4 3.683 4 4.5V17a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"}],["line",{x1:"10",x2:"8",y1:"5",y2:"7"}],["line",{x1:"2",x2:"22",y1:"12",y2:"12"}],["line",{x1:"7",x2:"7",y1:"19",y2:"21"}],["line",{x1:"17",x2:"17",y1:"19",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gr=["svg",o,[["path",{d:"M15 7h1a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"}],["path",{d:"M6 7H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h1"}],["path",{d:"m11 7-3 5h4l-3 5"}],["line",{x1:"22",x2:"22",y1:"11",y2:"13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xr=["svg",o,[["rect",{width:"16",height:"10",x:"2",y:"7",rx:"2",ry:"2"}],["line",{x1:"22",x2:"22",y1:"11",y2:"13"}],["line",{x1:"6",x2:"6",y1:"11",y2:"13"}],["line",{x1:"10",x2:"10",y1:"11",y2:"13"}],["line",{x1:"14",x2:"14",y1:"11",y2:"13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yr=["svg",o,[["rect",{width:"16",height:"10",x:"2",y:"7",rx:"2",ry:"2"}],["line",{x1:"22",x2:"22",y1:"11",y2:"13"}],["line",{x1:"6",x2:"6",y1:"11",y2:"13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kr=["svg",o,[["rect",{width:"16",height:"10",x:"2",y:"7",rx:"2",ry:"2"}],["line",{x1:"22",x2:"22",y1:"11",y2:"13"}],["line",{x1:"6",x2:"6",y1:"11",y2:"13"}],["line",{x1:"10",x2:"10",y1:"11",y2:"13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jr=["svg",o,[["path",{d:"M14 7h2a2 2 0 0 1 2 2v6c0 1-1 2-2 2h-2"}],["path",{d:"M6 7H4a2 2 0 0 0-2 2v6c0 1 1 2 2 2h2"}],["line",{x1:"22",x2:"22",y1:"11",y2:"13"}],["line",{x1:"10",x2:"10",y1:"7",y2:"13"}],["line",{x1:"10",x2:"10",y1:"17",y2:"17.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qr=["svg",o,[["rect",{width:"16",height:"10",x:"2",y:"7",rx:"2",ry:"2"}],["line",{x1:"22",x2:"22",y1:"11",y2:"13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t0=["svg",o,[["path",{d:"M4.5 3h15"}],["path",{d:"M6 3v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V3"}],["path",{d:"M6 14h12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e0=["svg",o,[["path",{d:"M9 9c-.64.64-1.521.954-2.402 1.165A6 6 0 0 0 8 22a13.96 13.96 0 0 0 9.9-4.1"}],["path",{d:"M10.75 5.093A6 6 0 0 1 22 8c0 2.411-.61 4.68-1.683 6.66"}],["path",{d:"M5.341 10.62a4 4 0 0 0 6.487 1.208M10.62 5.341a4.015 4.015 0 0 1 2.039 2.04"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s0=["svg",o,[["path",{d:"M10.165 6.598C9.954 7.478 9.64 8.36 9 9c-.64.64-1.521.954-2.402 1.165A6 6 0 0 0 8 22c7.732 0 14-6.268 14-14a6 6 0 0 0-11.835-1.402Z"}],["path",{d:"M5.341 10.62a4 4 0 1 0 5.279-5.28"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a0=["svg",o,[["path",{d:"M2 20v-8a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v8"}],["path",{d:"M4 10V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4"}],["path",{d:"M12 4v6"}],["path",{d:"M2 18h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i0=["svg",o,[["path",{d:"M3 20v-8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v8"}],["path",{d:"M5 10V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"}],["path",{d:"M3 18h18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n0=["svg",o,[["path",{d:"M2 4v16"}],["path",{d:"M2 8h18a2 2 0 0 1 2 2v10"}],["path",{d:"M2 17h20"}],["path",{d:"M6 8v9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o0=["svg",o,[["circle",{cx:"12.5",cy:"8.5",r:"2.5"}],["path",{d:"M12.5 2a6.5 6.5 0 0 0-6.22 4.6c-1.1 3.13-.78 3.9-3.18 6.08A3 3 0 0 0 5 18c4 0 8.4-1.8 11.4-4.3A6.5 6.5 0 0 0 12.5 2Z"}],["path",{d:"m18.5 6 2.19 4.5a6.48 6.48 0 0 1 .31 2 6.49 6.49 0 0 1-2.6 5.2C15.4 20.2 11 22 7 22a3 3 0 0 1-2.68-1.66L2.4 16.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r0=["svg",o,[["path",{d:"M17 11h1a3 3 0 0 1 0 6h-1"}],["path",{d:"M9 12v6"}],["path",{d:"M13 12v6"}],["path",{d:"M14 7.5c-1 0-1.44.5-3 .5s-2-.5-3-.5-1.72.5-2.5.5a2.5 2.5 0 0 1 0-5c.78 0 1.57.5 2.5.5S9.44 2 11 2s2 1.5 3 1.5 1.72-.5 2.5-.5a2.5 2.5 0 0 1 0 5c-.78 0-1.5-.5-2.5-.5Z"}],["path",{d:"M5 8v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h0=["svg",o,[["path",{d:"M19.4 14.9C20.2 16.4 21 17 21 17H3s3-2 3-9c0-3.3 2.7-6 6-6 .7 0 1.3.1 1.9.3"}],["path",{d:"M10.3 21a1.94 1.94 0 0 0 3.4 0"}],["circle",{cx:"18",cy:"8",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c0=["svg",o,[["path",{d:"M18.4 12c.8 3.8 2.6 5 2.6 5H3s3-2 3-9c0-3.3 2.7-6 6-6 1.8 0 3.4.8 4.5 2"}],["path",{d:"M10.3 21a1.94 1.94 0 0 0 3.4 0"}],["path",{d:"M15 8h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l0=["svg",o,[["path",{d:"M8.7 3A6 6 0 0 1 18 8a21.3 21.3 0 0 0 .6 5"}],["path",{d:"M17 17H3s3-2 3-9a4.67 4.67 0 0 1 .3-1.7"}],["path",{d:"M10.3 21a1.94 1.94 0 0 0 3.4 0"}],["path",{d:"m2 2 20 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d0=["svg",o,[["path",{d:"M19.3 14.8C20.1 16.4 21 17 21 17H3s3-2 3-9c0-3.3 2.7-6 6-6 1 0 1.9.2 2.8.7"}],["path",{d:"M10.3 21a1.94 1.94 0 0 0 3.4 0"}],["path",{d:"M15 8h6"}],["path",{d:"M18 5v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p0=["svg",o,[["path",{d:"M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"}],["path",{d:"M10.3 21a1.94 1.94 0 0 0 3.4 0"}],["path",{d:"M4 2C2.8 3.7 2 5.7 2 8"}],["path",{d:"M22 8c0-2.3-.8-4.3-2-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g0=["svg",o,[["path",{d:"M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"}],["path",{d:"M10.3 21a1.94 1.94 0 0 0 3.4 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u0=["svg",o,[["circle",{cx:"18.5",cy:"17.5",r:"3.5"}],["circle",{cx:"5.5",cy:"17.5",r:"3.5"}],["circle",{cx:"15",cy:"5",r:"1"}],["path",{d:"M12 17.5V14l-3-3 4-3 2 3h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f0=["svg",o,[["rect",{x:"14",y:"14",width:"4",height:"6",rx:"2"}],["rect",{x:"6",y:"4",width:"4",height:"6",rx:"2"}],["path",{d:"M6 20h4"}],["path",{d:"M14 10h4"}],["path",{d:"M6 14h2v6"}],["path",{d:"M14 4h2v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v0=["svg",o,[["circle",{cx:"12",cy:"11.9",r:"2"}],["path",{d:"M6.7 3.4c-.9 2.5 0 5.2 2.2 6.7C6.5 9 3.7 9.6 2 11.6"}],["path",{d:"m8.9 10.1 1.4.8"}],["path",{d:"M17.3 3.4c.9 2.5 0 5.2-2.2 6.7 2.4-1.2 5.2-.6 6.9 1.5"}],["path",{d:"m15.1 10.1-1.4.8"}],["path",{d:"M16.7 20.8c-2.6-.4-4.6-2.6-4.7-5.3-.2 2.6-2.1 4.8-4.7 5.2"}],["path",{d:"M12 13.9v1.6"}],["path",{d:"M13.5 5.4c-1-.2-2-.2-3 0"}],["path",{d:"M17 16.4c.7-.7 1.2-1.6 1.5-2.5"}],["path",{d:"M5.5 13.9c.3.9.8 1.8 1.5 2.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x0=["svg",o,[["path",{d:"M16 7h.01"}],["path",{d:"M3.4 18H12a8 8 0 0 0 8-8V7a4 4 0 0 0-7.28-2.3L2 20"}],["path",{d:"m20 7 2 .5-2 .5"}],["path",{d:"M10 18v3"}],["path",{d:"M14 17.75V21"}],["path",{d:"M7 18a6 6 0 0 0 3.84-10.61"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m0=["svg",o,[["path",{d:"M11.767 19.089c4.924.868 6.14-6.025 1.216-6.894m-1.216 6.894L5.86 18.047m5.908 1.042-.347 1.97m1.563-8.864c4.924.869 6.14-6.025 1.215-6.893m-1.215 6.893-3.94-.694m5.155-6.2L8.29 4.26m5.908 1.042.348-1.97M7.48 20.364l3.126-17.727"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M0=["svg",o,[["path",{d:"M3 3h18"}],["path",{d:"M20 7H8"}],["path",{d:"M20 11H8"}],["path",{d:"M10 19h10"}],["path",{d:"M8 15h12"}],["path",{d:"M4 3v14"}],["circle",{cx:"4",cy:"19",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y0=["svg",o,[["rect",{width:"7",height:"7",x:"14",y:"3",rx:"1"}],["path",{d:"M10 21V8a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5a1 1 0 0 0-1-1H3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b0=["svg",o,[["path",{d:"m7 7 10 10-5 5V2l5 5L7 17"}],["line",{x1:"18",x2:"21",y1:"12",y2:"12"}],["line",{x1:"3",x2:"6",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w0=["svg",o,[["path",{d:"m17 17-5 5V12l-5 5"}],["path",{d:"m2 2 20 20"}],["path",{d:"M14.5 9.5 17 7l-5-5v4.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _0=["svg",o,[["path",{d:"m7 7 10 10-5 5V2l5 5L7 17"}],["path",{d:"M20.83 14.83a4 4 0 0 0 0-5.66"}],["path",{d:"M18 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k0=["svg",o,[["path",{d:"m7 7 10 10-5 5V2l5 5L7 17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C0=["svg",o,[["path",{d:"M14 12a4 4 0 0 0 0-8H6v8"}],["path",{d:"M15 20a4 4 0 0 0 0-8H6v8Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S0=["svg",o,[["circle",{cx:"11",cy:"13",r:"9"}],["path",{d:"M14.35 4.65 16.3 2.7a2.41 2.41 0 0 1 3.4 0l1.6 1.6a2.4 2.4 0 0 1 0 3.4l-1.95 1.95"}],["path",{d:"m22 2-1.5 1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L0=["svg",o,[["path",{d:"M17 10c.7-.7 1.69 0 2.5 0a2.5 2.5 0 1 0 0-5 .5.5 0 0 1-.5-.5 2.5 2.5 0 1 0-5 0c0 .81.7 1.8 0 2.5l-7 7c-.7.7-1.69 0-2.5 0a2.5 2.5 0 0 0 0 5c.28 0 .5.22.5.5a2.5 2.5 0 1 0 5 0c0-.81-.7-1.8 0-2.5Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"m8 13 4-7 4 7"}],["path",{d:"M9.1 11h5.7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M8 8v3"}],["path",{d:"M12 6v7"}],["path",{d:"M16 8v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"m9 9.5 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P0=["svg",o,[["path",{d:"M2 16V4a2 2 0 0 1 2-2h11"}],["path",{d:"M5 14H4a2 2 0 1 0 0 4h1"}],["path",{d:"M22 18H11a2 2 0 1 0 0 4h11V6H11a2 2 0 0 0-2 2v12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bs=["svg",o,[["path",{d:"M20 22h-2"}],["path",{d:"M20 15v2h-2"}],["path",{d:"M4 19.5V15"}],["path",{d:"M20 8v3"}],["path",{d:"M18 2h2v2"}],["path",{d:"M4 11V9"}],["path",{d:"M12 2h2"}],["path",{d:"M12 22h2"}],["path",{d:"M12 17h2"}],["path",{d:"M8 22H6.5a2.5 2.5 0 0 1 0-5H8"}],["path",{d:"M4 5v-.5A2.5 2.5 0 0 1 6.5 2H8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M12 13V7"}],["path",{d:"m9 10 3 3 3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["circle",{cx:"9",cy:"12",r:"1"}],["path",{d:"M8 12v-2a4 4 0 0 1 8 0v2"}],["circle",{cx:"15",cy:"12",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M16 8.2C16 7 15 6 13.8 6c-.8 0-1.4.3-1.8.9-.4-.6-1-.9-1.8-.9C9 6 8 7 8 8.2c0 .6.3 1.2.7 1.6h0C10 11.1 12 13 12 13s2-1.9 3.3-3.1h0c.4-.4.7-1 .7-1.7z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["circle",{cx:"10",cy:"8",r:"2"}],["path",{d:"m20 13.7-2.1-2.1c-.8-.8-2-.8-2.8 0L9.7 17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H14"}],["path",{d:"M20 8v14H6.5a2.5 2.5 0 0 1 0-5H20"}],["circle",{cx:"14",cy:"8",r:"2"}],["path",{d:"m20 2-4.5 4.5"}],["path",{d:"m19 3 1 1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H10"}],["path",{d:"M20 15v7H6.5a2.5 2.5 0 0 1 0-5H20"}],["rect",{width:"8",height:"5",x:"12",y:"6",rx:"1"}],["path",{d:"M18 6V4a2 2 0 1 0-4 0v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["polyline",{points:"10 2 10 10 13 7 16 10 16 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M9 10h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I0=["svg",o,[["path",{d:"M8 3H2v15h7c1.7 0 3 1.3 3 3V7c0-2.2-1.8-4-4-4Z"}],["path",{d:"m16 12 2 2 4-4"}],["path",{d:"M22 6V3h-6c-2.2 0-4 1.8-4 4v14c0-1.7 1.3-3 3-3h7v-2.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $0=["svg",o,[["path",{d:"M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"}],["path",{d:"M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"}],["path",{d:"M6 8h2"}],["path",{d:"M6 12h2"}],["path",{d:"M16 8h2"}],["path",{d:"M16 12h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z0=["svg",o,[["path",{d:"M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"}],["path",{d:"M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M9 10h6"}],["path",{d:"M12 7v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M8 7h6"}],["path",{d:"M8 11h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M16 8V6H8v2"}],["path",{d:"M12 6v7"}],["path",{d:"M10 13h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2"}],["path",{d:"M18 2h2v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M12 13V7"}],["path",{d:"m9 10 3-3 3 3"}],["path",{d:"m9 5 3-3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"M12 13V7"}],["path",{d:"m9 10 3-3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["circle",{cx:"12",cy:"8",r:"2"}],["path",{d:"M15 13a3 3 0 1 0-6 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}],["path",{d:"m14.5 7-5 5"}],["path",{d:"m9.5 7 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y0=["svg",o,[["path",{d:"M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K0=["svg",o,[["path",{d:"m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z"}],["path",{d:"m9 10 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J0=["svg",o,[["path",{d:"m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"}],["line",{x1:"15",x2:"9",y1:"10",y2:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q0=["svg",o,[["path",{d:"m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"}],["line",{x1:"12",x2:"12",y1:"7",y2:"13"}],["line",{x1:"15",x2:"9",y1:"10",y2:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const th=["svg",o,[["path",{d:"m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z"}],["path",{d:"m14.5 7.5-5 5"}],["path",{d:"m9.5 7.5 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const eh=["svg",o,[["path",{d:"m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sh=["svg",o,[["path",{d:"M4 9V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4"}],["path",{d:"M8 8v1"}],["path",{d:"M12 8v1"}],["path",{d:"M16 8v1"}],["rect",{width:"20",height:"12",x:"2",y:"9",rx:"2"}],["circle",{cx:"8",cy:"15",r:"2"}],["circle",{cx:"16",cy:"15",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ah=["svg",o,[["path",{d:"M12 8V4H8"}],["rect",{width:"16",height:"12",x:"4",y:"8",rx:"2"}],["path",{d:"M2 14h2"}],["path",{d:"M20 14h2"}],["path",{d:"M15 13v2"}],["path",{d:"M9 13v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ih=["svg",o,[["path",{d:"M5 3a2 2 0 0 0-2 2"}],["path",{d:"M19 3a2 2 0 0 1 2 2"}],["path",{d:"M21 19a2 2 0 0 1-2 2"}],["path",{d:"M5 21a2 2 0 0 1-2-2"}],["path",{d:"M9 3h1"}],["path",{d:"M9 21h1"}],["path",{d:"M14 3h1"}],["path",{d:"M14 21h1"}],["path",{d:"M3 9v1"}],["path",{d:"M21 9v1"}],["path",{d:"M3 14v1"}],["path",{d:"M21 14v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nh=["svg",o,[["path",{d:"M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"}],["path",{d:"m3.3 7 8.7 5 8.7-5"}],["path",{d:"M12 22V12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const oh=["svg",o,[["path",{d:"M2.97 12.92A2 2 0 0 0 2 14.63v3.24a2 2 0 0 0 .97 1.71l3 1.8a2 2 0 0 0 2.06 0L12 19v-5.5l-5-3-4.03 2.42Z"}],["path",{d:"m7 16.5-4.74-2.85"}],["path",{d:"m7 16.5 5-3"}],["path",{d:"M7 16.5v5.17"}],["path",{d:"M12 13.5V19l3.97 2.38a2 2 0 0 0 2.06 0l3-1.8a2 2 0 0 0 .97-1.71v-3.24a2 2 0 0 0-.97-1.71L17 10.5l-5 3Z"}],["path",{d:"m17 16.5-5-3"}],["path",{d:"m17 16.5 4.74-2.85"}],["path",{d:"M17 16.5v5.17"}],["path",{d:"M7.97 4.42A2 2 0 0 0 7 6.13v4.37l5 3 5-3V6.13a2 2 0 0 0-.97-1.71l-3-1.8a2 2 0 0 0-2.06 0l-3 1.8Z"}],["path",{d:"M12 8 7.26 5.15"}],["path",{d:"m12 8 4.74-2.85"}],["path",{d:"M12 13.5V8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Os=["svg",o,[["path",{d:"M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1"}],["path",{d:"M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rh=["svg",o,[["path",{d:"M16 3h3v18h-3"}],["path",{d:"M8 21H5V3h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hh=["svg",o,[["path",{d:"M12 4.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0-1.32 4.24 3 3 0 0 0 .34 5.58 2.5 2.5 0 0 0 2.96 3.08 2.5 2.5 0 0 0 4.91.05L12 20V4.5Z"}],["path",{d:"M16 8V5c0-1.1.9-2 2-2"}],["path",{d:"M12 13h4"}],["path",{d:"M12 18h6a2 2 0 0 1 2 2v1"}],["path",{d:"M12 8h8"}],["path",{d:"M20.5 8a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"}],["path",{d:"M16.5 13a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"}],["path",{d:"M20.5 21a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"}],["path",{d:"M18.5 3a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ch=["svg",o,[["circle",{cx:"12",cy:"12",r:"3"}],["path",{d:"M12 4.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0-1.32 4.24 3 3 0 0 0 .34 5.58 2.5 2.5 0 0 0 2.96 3.08A2.5 2.5 0 0 0 12 19.5a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 12 4.5"}],["path",{d:"m15.7 10.4-.9.4"}],["path",{d:"m9.2 13.2-.9.4"}],["path",{d:"m13.6 15.7-.4-.9"}],["path",{d:"m10.8 9.2-.4-.9"}],["path",{d:"m15.7 13.5-.9-.4"}],["path",{d:"m9.2 10.9-.9-.4"}],["path",{d:"m10.5 15.7.4-.9"}],["path",{d:"m13.1 9.2.4-.9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lh=["svg",o,[["path",{d:"M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"}],["path",{d:"M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dh=["svg",o,[["rect",{width:"20",height:"14",x:"2",y:"7",rx:"2",ry:"2"}],["path",{d:"M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ph=["svg",o,[["rect",{x:"8",y:"8",width:"8",height:"8",rx:"2"}],["path",{d:"M4 10a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2"}],["path",{d:"M14 20a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gh=["svg",o,[["path",{d:"m9.06 11.9 8.07-8.06a2.85 2.85 0 1 1 4.03 4.03l-8.06 8.08"}],["path",{d:"M7.07 14.94c-1.66 0-3 1.35-3 3.02 0 1.33-2.5 1.52-2 2.02 1.08 1.1 2.49 2.02 4 2.02 2.2 0 4-1.8 4-4.04a3.01 3.01 0 0 0-3-3.02z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uh=["svg",o,[["path",{d:"M15 7.13V6a3 3 0 0 0-5.14-2.1L8 2"}],["path",{d:"M14.12 3.88 16 2"}],["path",{d:"M22 13h-4v-2a4 4 0 0 0-4-4h-1.3"}],["path",{d:"M20.97 5c0 2.1-1.6 3.8-3.5 4"}],["path",{d:"m2 2 20 20"}],["path",{d:"M7.7 7.7A4 4 0 0 0 6 11v3a6 6 0 0 0 11.13 3.13"}],["path",{d:"M12 20v-8"}],["path",{d:"M6 13H2"}],["path",{d:"M3 21c0-2.1 1.7-3.9 3.8-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fh=["svg",o,[["path",{d:"m8 2 1.88 1.88"}],["path",{d:"M14.12 3.88 16 2"}],["path",{d:"M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"}],["path",{d:"M18 11a4 4 0 0 0-4-4h-4a4 4 0 0 0-4 4v3a6.1 6.1 0 0 0 2 4.5"}],["path",{d:"M6.53 9C4.6 8.8 3 7.1 3 5"}],["path",{d:"M6 13H2"}],["path",{d:"M3 21c0-2.1 1.7-3.9 3.8-4"}],["path",{d:"M20.97 5c0 2.1-1.6 3.8-3.5 4"}],["path",{d:"m12 12 8 5-8 5Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vh=["svg",o,[["path",{d:"m8 2 1.88 1.88"}],["path",{d:"M14.12 3.88 16 2"}],["path",{d:"M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"}],["path",{d:"M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"}],["path",{d:"M12 20v-9"}],["path",{d:"M6.53 9C4.6 8.8 3 7.1 3 5"}],["path",{d:"M6 13H2"}],["path",{d:"M3 21c0-2.1 1.7-3.9 3.8-4"}],["path",{d:"M20.97 5c0 2.1-1.6 3.8-3.5 4"}],["path",{d:"M22 13h-4"}],["path",{d:"M17.2 17c2.1.1 3.8 1.9 3.8 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xh=["svg",o,[["path",{d:"M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"}],["path",{d:"M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"}],["path",{d:"M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"}],["path",{d:"M10 6h4"}],["path",{d:"M10 10h4"}],["path",{d:"M10 14h4"}],["path",{d:"M10 18h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mh=["svg",o,[["rect",{width:"16",height:"20",x:"4",y:"2",rx:"2",ry:"2"}],["path",{d:"M9 22v-4h6v4"}],["path",{d:"M8 6h.01"}],["path",{d:"M16 6h.01"}],["path",{d:"M12 6h.01"}],["path",{d:"M12 10h.01"}],["path",{d:"M12 14h.01"}],["path",{d:"M16 10h.01"}],["path",{d:"M16 14h.01"}],["path",{d:"M8 10h.01"}],["path",{d:"M8 14h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mh=["svg",o,[["path",{d:"M4 6 2 7"}],["path",{d:"M10 6h4"}],["path",{d:"m22 7-2-1"}],["rect",{width:"16",height:"16",x:"4",y:"3",rx:"2"}],["path",{d:"M4 11h16"}],["path",{d:"M8 15h.01"}],["path",{d:"M16 15h.01"}],["path",{d:"M6 19v2"}],["path",{d:"M18 21v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yh=["svg",o,[["path",{d:"M8 6v6"}],["path",{d:"M15 6v6"}],["path",{d:"M2 12h19.6"}],["path",{d:"M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H4a2 2 0 0 0-2 2v10h3"}],["circle",{cx:"7",cy:"18",r:"2"}],["path",{d:"M9 18h5"}],["circle",{cx:"16",cy:"18",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bh=["svg",o,[["path",{d:"M10 3h.01"}],["path",{d:"M14 2h.01"}],["path",{d:"m2 9 20-5"}],["path",{d:"M12 12V6.5"}],["rect",{width:"16",height:"10",x:"4",y:"12",rx:"3"}],["path",{d:"M9 12v5"}],["path",{d:"M15 12v5"}],["path",{d:"M4 17h16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wh=["svg",o,[["path",{d:"M4 9a2 2 0 0 1-2-2V5h6v2a2 2 0 0 1-2 2Z"}],["path",{d:"M3 5V3"}],["path",{d:"M7 5V3"}],["path",{d:"M19 15V6.5a3.5 3.5 0 0 0-7 0v11a3.5 3.5 0 0 1-7 0V9"}],["path",{d:"M17 21v-2"}],["path",{d:"M21 21v-2"}],["path",{d:"M22 19h-6v-2a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _h=["svg",o,[["circle",{cx:"9",cy:"7",r:"2"}],["path",{d:"M7.2 7.9 3 11v9c0 .6.4 1 1 1h16c.6 0 1-.4 1-1v-9c0-2-3-6-7-8l-3.6 2.6"}],["path",{d:"M16 13H3"}],["path",{d:"M16 17H3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kh=["svg",o,[["path",{d:"M20 21v-8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8"}],["path",{d:"M4 16s.5-1 2-1 2.5 2 4 2 2.5-2 4-2 2.5 2 4 2 2-1 2-1"}],["path",{d:"M2 21h20"}],["path",{d:"M7 8v3"}],["path",{d:"M12 8v3"}],["path",{d:"M17 8v3"}],["path",{d:"M7 4h0.01"}],["path",{d:"M12 4h0.01"}],["path",{d:"M17 4h0.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ch=["svg",o,[["rect",{width:"16",height:"20",x:"4",y:"2",rx:"2"}],["line",{x1:"8",x2:"16",y1:"6",y2:"6"}],["line",{x1:"16",x2:"16",y1:"14",y2:"18"}],["path",{d:"M16 10h.01"}],["path",{d:"M12 10h.01"}],["path",{d:"M8 10h.01"}],["path",{d:"M12 14h.01"}],["path",{d:"M8 14h.01"}],["path",{d:"M12 18h.01"}],["path",{d:"M8 18h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sh=["svg",o,[["path",{d:"M21 14V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["path",{d:"m16 20 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lh=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",ry:"2"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["path",{d:"m9 16 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ah=["svg",o,[["path",{d:"M21 7.5V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h3.5"}],["path",{d:"M16 2v4"}],["path",{d:"M8 2v4"}],["path",{d:"M3 10h5"}],["path",{d:"M17.5 17.5 16 16.25V14"}],["path",{d:"M22 16a6 6 0 1 1-12 0 6 6 0 0 1 12 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hh=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",ry:"2"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["path",{d:"M8 14h.01"}],["path",{d:"M12 14h.01"}],["path",{d:"M16 14h.01"}],["path",{d:"M8 18h.01"}],["path",{d:"M12 18h.01"}],["path",{d:"M16 18h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vh=["svg",o,[["path",{d:"M21 10V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h7"}],["path",{d:"M16 2v4"}],["path",{d:"M8 2v4"}],["path",{d:"M3 10h18"}],["path",{d:"M21.29 14.7a2.43 2.43 0 0 0-2.65-.52c-.3.12-.57.3-.8.53l-.34.34-.35-.34a2.43 2.43 0 0 0-2.65-.53c-.3.12-.56.3-.79.53-.95.94-1 2.53.2 3.74L17.5 22l3.6-3.55c1.2-1.21 1.14-2.8.19-3.74Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ph=["svg",o,[["path",{d:"M21 13V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["line",{x1:"16",x2:"22",y1:"19",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dh=["svg",o,[["path",{d:"M4.18 4.18A2 2 0 0 0 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 1.82-1.18"}],["path",{d:"M21 15.5V6a2 2 0 0 0-2-2H9.5"}],["path",{d:"M16 2v4"}],["path",{d:"M3 10h7"}],["path",{d:"M21 10h-5.5"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fh=["svg",o,[["path",{d:"M21 13V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["line",{x1:"19",x2:"19",y1:"16",y2:"22"}],["line",{x1:"16",x2:"22",y1:"19",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Th=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",ry:"2"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["path",{d:"M17 14h-6"}],["path",{d:"M13 18H7"}],["path",{d:"M7 14h.01"}],["path",{d:"M17 18h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bh=["svg",o,[["path",{d:"M21 12V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h7.5"}],["path",{d:"M16 2v4"}],["path",{d:"M8 2v4"}],["path",{d:"M3 10h18"}],["path",{d:"M18 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6v0Z"}],["path",{d:"m22 22-1.5-1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Oh=["svg",o,[["path",{d:"M21 13V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["line",{x1:"17",x2:"22",y1:"17",y2:"22"}],["line",{x1:"17",x2:"22",y1:"22",y2:"17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Eh=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",ry:"2"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}],["line",{x1:"10",x2:"14",y1:"14",y2:"18"}],["line",{x1:"14",x2:"10",y1:"14",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rh=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",ry:"2"}],["line",{x1:"16",x2:"16",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"2",y2:"6"}],["line",{x1:"3",x2:"21",y1:"10",y2:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zh=["svg",o,[["line",{x1:"2",x2:"22",y1:"2",y2:"22"}],["path",{d:"M7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16"}],["path",{d:"M9.5 4h5L17 7h3a2 2 0 0 1 2 2v7.5"}],["path",{d:"M14.121 15.121A3 3 0 1 1 9.88 10.88"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ih=["svg",o,[["path",{d:"M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"}],["circle",{cx:"12",cy:"13",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $h=["svg",o,[["path",{d:"M9 5v4"}],["rect",{width:"4",height:"6",x:"7",y:"9",rx:"1"}],["path",{d:"M9 15v2"}],["path",{d:"M17 3v2"}],["rect",{width:"4",height:"8",x:"15",y:"5",rx:"1"}],["path",{d:"M17 13v3"}],["path",{d:"M3 3v18h18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zh=["svg",o,[["path",{d:"M5.7 21a2 2 0 0 1-3.5-2l8.6-14a6 6 0 0 1 10.4 6 2 2 0 1 1-3.464-2 2 2 0 1 0-3.464-2Z"}],["path",{d:"M17.75 7 15 2.1"}],["path",{d:"M10.9 4.8 13 9"}],["path",{d:"m7.9 9.7 2 4.4"}],["path",{d:"M4.9 14.7 7 18.9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wh=["svg",o,[["path",{d:"m8.5 8.5-1 1a4.95 4.95 0 0 0 7 7l1-1"}],["path",{d:"M11.843 6.187A4.947 4.947 0 0 1 16.5 7.5a4.947 4.947 0 0 1 1.313 4.657"}],["path",{d:"M14 16.5V14"}],["path",{d:"M14 6.5v1.843"}],["path",{d:"M10 10v7.5"}],["path",{d:"m16 7 1-5 1.367.683A3 3 0 0 0 19.708 3H21v1.292a3 3 0 0 0 .317 1.341L22 7l-5 1"}],["path",{d:"m8 17-1 5-1.367-.683A3 3 0 0 0 4.292 21H3v-1.292a3 3 0 0 0-.317-1.341L2 17l5-1"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nh=["svg",o,[["path",{d:"m9.5 7.5-2 2a4.95 4.95 0 1 0 7 7l2-2a4.95 4.95 0 1 0-7-7Z"}],["path",{d:"M14 6.5v10"}],["path",{d:"M10 7.5v10"}],["path",{d:"m16 7 1-5 1.37.68A3 3 0 0 0 19.7 3H21v1.3c0 .46.1.92.32 1.33L22 7l-5 1"}],["path",{d:"m8 17-1 5-1.37-.68A3 3 0 0 0 4.3 21H3v-1.3a3 3 0 0 0-.32-1.33L2 17l5-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jh=["svg",o,[["path",{d:"m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"}],["path",{d:"M7 14h.01"}],["path",{d:"M17 14h.01"}],["rect",{width:"18",height:"8",x:"3",y:"10",rx:"2"}],["path",{d:"M5 18v2"}],["path",{d:"M19 18v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uh=["svg",o,[["path",{d:"M10 2h4"}],["path",{d:"m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"}],["path",{d:"M7 14h.01"}],["path",{d:"M17 14h.01"}],["rect",{width:"18",height:"8",x:"3",y:"10",rx:"2"}],["path",{d:"M5 18v2"}],["path",{d:"M19 18v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qh=["svg",o,[["path",{d:"M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"}],["circle",{cx:"7",cy:"17",r:"2"}],["path",{d:"M9 17h6"}],["circle",{cx:"17",cy:"17",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gh=["svg",o,[["rect",{width:"4",height:"4",x:"2",y:"9"}],["rect",{width:"4",height:"10",x:"10",y:"9"}],["path",{d:"M18 19V9a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v8a2 2 0 0 0 2 2h2"}],["circle",{cx:"8",cy:"19",r:"2"}],["path",{d:"M10 19h12v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xh=["svg",o,[["path",{d:"M2.27 21.7s9.87-3.5 12.73-6.36a4.5 4.5 0 0 0-6.36-6.37C5.77 11.84 2.27 21.7 2.27 21.7zM8.64 14l-2.05-2.04M15.34 15l-2.46-2.46"}],["path",{d:"M22 9s-1.33-2-3.5-2C16.86 7 15 9 15 9s1.33 2 3.5 2S22 9 22 9z"}],["path",{d:"M15 2s-2 1.33-2 3.5S15 9 15 9s2-1.84 2-3.5C17 3.33 15 2 15 2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yh=["svg",o,[["circle",{cx:"7",cy:"12",r:"3"}],["path",{d:"M10 9v6"}],["circle",{cx:"17",cy:"12",r:"3"}],["path",{d:"M14 7v8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kh=["svg",o,[["path",{d:"m3 15 4-8 4 8"}],["path",{d:"M4 13h6"}],["circle",{cx:"18",cy:"12",r:"3"}],["path",{d:"M21 9v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jh=["svg",o,[["path",{d:"m3 15 4-8 4 8"}],["path",{d:"M4 13h6"}],["path",{d:"M15 11h4.5a2 2 0 0 1 0 4H15V7h4a2 2 0 0 1 0 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qh=["svg",o,[["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}],["circle",{cx:"8",cy:"10",r:"2"}],["path",{d:"M8 12h8"}],["circle",{cx:"16",cy:"10",r:"2"}],["path",{d:"m6 20 .7-2.9A1.4 1.4 0 0 1 8.1 16h7.8a1.4 1.4 0 0 1 1.4 1l.7 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tc=["svg",o,[["path",{d:"M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"}],["path",{d:"M2 12a9 9 0 0 1 8 8"}],["path",{d:"M2 16a5 5 0 0 1 4 4"}],["line",{x1:"2",x2:"2.01",y1:"20",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ec=["svg",o,[["path",{d:"M22 20v-9H2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2Z"}],["path",{d:"M18 11V4H6v7"}],["path",{d:"M15 22v-4a3 3 0 0 0-3-3v0a3 3 0 0 0-3 3v4"}],["path",{d:"M22 11V9"}],["path",{d:"M2 11V9"}],["path",{d:"M6 4V2"}],["path",{d:"M18 4V2"}],["path",{d:"M10 4V2"}],["path",{d:"M14 4V2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sc=["svg",o,[["path",{d:"M12 5c.67 0 1.35.09 2 .26 1.78-2 5.03-2.84 6.42-2.26 1.4.58-.42 7-.42 7 .57 1.07 1 2.24 1 3.44C21 17.9 16.97 21 12 21s-9-3-9-7.56c0-1.25.5-2.4 1-3.44 0 0-1.89-6.42-.5-7 1.39-.58 4.72.23 6.5 2.23A9.04 9.04 0 0 1 12 5Z"}],["path",{d:"M8 14v.5"}],["path",{d:"M16 14v.5"}],["path",{d:"M11.25 16.25h1.5L12 17l-.75-.75Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ac=["svg",o,[["path",{d:"M18 6 7 17l-5-5"}],["path",{d:"m22 10-7.5 7.5L13 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ic=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nc=["svg",o,[["path",{d:"M22 11.08V12a10 10 0 1 1-5.93-9.14"}],["path",{d:"m9 11 3 3L22 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const oc=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m9 12 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rc=["svg",o,[["path",{d:"m9 11 3 3L22 4"}],["path",{d:"M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hc=["svg",o,[["path",{d:"M20 6 9 17l-5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cc=["svg",o,[["path",{d:"M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6Z"}],["line",{x1:"6",x2:"18",y1:"17",y2:"17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lc=["svg",o,[["path",{d:"M2 17a5 5 0 0 0 10 0c0-2.76-2.5-5-5-3-2.5-2-5 .24-5 3Z"}],["path",{d:"M12 17a5 5 0 0 0 10 0c0-2.76-2.5-5-5-3-2.5-2-5 .24-5 3Z"}],["path",{d:"M7 14c3.22-2.91 4.29-8.75 5-12 1.66 2.38 4.94 9 5 12"}],["path",{d:"M22 9c-4.29 0-7.14-2.33-10-7 5.71 0 10 4.67 10 7Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dc=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m16 10-4 4-4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pc=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m16 10-4 4-4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gc=["svg",o,[["path",{d:"m6 9 6 6 6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uc=["svg",o,[["path",{d:"m17 18-6-6 6-6"}],["path",{d:"M7 6v12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fc=["svg",o,[["path",{d:"m7 18 6-6-6-6"}],["path",{d:"M17 6v12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vc=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m14 16-4-4 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xc=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m14 16-4-4 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mc=["svg",o,[["path",{d:"m15 18-6-6 6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mc=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m10 8 4 4-4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yc=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m10 8 4 4-4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bc=["svg",o,[["path",{d:"m9 18 6-6-6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wc=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m8 14 4-4 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _c=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m8 14 4-4 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kc=["svg",o,[["path",{d:"m18 15-6-6-6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cc=["svg",o,[["path",{d:"m7 20 5-5 5 5"}],["path",{d:"m7 4 5 5 5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sc=["svg",o,[["path",{d:"m7 6 5 5 5-5"}],["path",{d:"m7 13 5 5 5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lc=["svg",o,[["path",{d:"m9 7-5 5 5 5"}],["path",{d:"m15 7 5 5-5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ac=["svg",o,[["path",{d:"m11 17-5-5 5-5"}],["path",{d:"m18 17-5-5 5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hc=["svg",o,[["path",{d:"m20 17-5-5 5-5"}],["path",{d:"m4 17 5-5-5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vc=["svg",o,[["path",{d:"m6 17 5-5-5-5"}],["path",{d:"m13 17 5-5-5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pc=["svg",o,[["path",{d:"m7 15 5 5 5-5"}],["path",{d:"m7 9 5-5 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dc=["svg",o,[["path",{d:"m17 11-5-5-5 5"}],["path",{d:"m17 18-5-5-5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fc=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["circle",{cx:"12",cy:"12",r:"4"}],["line",{x1:"21.17",x2:"12",y1:"8",y2:"8"}],["line",{x1:"3.95",x2:"8.54",y1:"6.06",y2:"14"}],["line",{x1:"10.88",x2:"15.46",y1:"21.94",y2:"14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tc=["svg",o,[["path",{d:"m18 7 4 2v11a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9l4-2"}],["path",{d:"M14 22v-4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v4"}],["path",{d:"M18 22V5l-6-3-6 3v17"}],["path",{d:"M12 7v5"}],["path",{d:"M10 9h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bc=["svg",o,[["line",{x1:"2",x2:"22",y1:"2",y2:"22"}],["path",{d:"M12 12H2v4h14"}],["path",{d:"M22 12v4"}],["path",{d:"M18 12h-.5"}],["path",{d:"M7 12v4"}],["path",{d:"M18 8c0-2.5-2-2.5-2-5"}],["path",{d:"M22 8c0-2.5-2-2.5-2-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Oc=["svg",o,[["path",{d:"M18 12H2v4h16"}],["path",{d:"M22 12v4"}],["path",{d:"M7 12v4"}],["path",{d:"M18 8c0-2.5-2-2.5-2-5"}],["path",{d:"M22 8c0-2.5-2-2.5-2-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ec=["svg",o,[["path",{d:"M10.1 2.18a9.93 9.93 0 0 1 3.8 0"}],["path",{d:"M17.6 3.71a9.95 9.95 0 0 1 2.69 2.7"}],["path",{d:"M21.82 10.1a9.93 9.93 0 0 1 0 3.8"}],["path",{d:"M20.29 17.6a9.95 9.95 0 0 1-2.7 2.69"}],["path",{d:"M13.9 21.82a9.94 9.94 0 0 1-3.8 0"}],["path",{d:"M6.4 20.29a9.95 9.95 0 0 1-2.69-2.7"}],["path",{d:"M2.18 13.9a9.93 9.93 0 0 1 0-3.8"}],["path",{d:"M3.71 6.4a9.95 9.95 0 0 1 2.7-2.69"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rc=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"}],["path",{d:"M12 18V6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zc=["svg",o,[["path",{d:"M10.1 2.18a9.93 9.93 0 0 1 3.8 0"}],["path",{d:"M17.6 3.71a9.95 9.95 0 0 1 2.69 2.7"}],["path",{d:"M21.82 10.1a9.93 9.93 0 0 1 0 3.8"}],["path",{d:"M20.29 17.6a9.95 9.95 0 0 1-2.7 2.69"}],["path",{d:"M13.9 21.82a9.94 9.94 0 0 1-3.8 0"}],["path",{d:"M6.4 20.29a9.95 9.95 0 0 1-2.69-2.7"}],["path",{d:"M2.18 13.9a9.93 9.93 0 0 1 0-3.8"}],["path",{d:"M3.71 6.4a9.95 9.95 0 0 1 2.7-2.69"}],["circle",{cx:"12",cy:"12",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ic=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["circle",{cx:"12",cy:"12",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $c=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M17 12h.01"}],["path",{d:"M12 12h.01"}],["path",{d:"M7 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zc=["svg",o,[["path",{d:"M7 10h10"}],["path",{d:"M7 14h10"}],["circle",{cx:"12",cy:"12",r:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wc=["svg",o,[["path",{d:"m2 2 20 20"}],["path",{d:"M8.35 2.69A10 10 0 0 1 21.3 15.65"}],["path",{d:"M19.08 19.08A10 10 0 1 1 4.92 4.92"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Es=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M22 2 2 22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nc=["svg",o,[["line",{x1:"9",x2:"15",y1:"15",y2:"9"}],["circle",{cx:"12",cy:"12",r:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rs=["svg",o,[["path",{d:"M18 20a6 6 0 0 0-12 0"}],["circle",{cx:"12",cy:"10",r:"4"}],["circle",{cx:"12",cy:"12",r:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zs=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["circle",{cx:"12",cy:"10",r:"3"}],["path",{d:"M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jc=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uc=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M11 9h4a2 2 0 0 0 2-2V3"}],["circle",{cx:"9",cy:"9",r:"2"}],["path",{d:"M7 21v-4a2 2 0 0 1 2-2h4"}],["circle",{cx:"15",cy:"15",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qc=["svg",o,[["path",{d:"M21.66 17.67a1.08 1.08 0 0 1-.04 1.6A12 12 0 0 1 4.73 2.38a1.1 1.1 0 0 1 1.61-.04z"}],["path",{d:"M19.65 15.66A8 8 0 0 1 8.35 4.34"}],["path",{d:"m14 10-5.5 5.5"}],["path",{d:"M14 17.85V10H6.15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gc=["svg",o,[["path",{d:"M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"}],["path",{d:"m6.2 5.3 3.1 3.9"}],["path",{d:"m12.4 3.4 3.1 4"}],["path",{d:"M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xc=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"}],["path",{d:"m9 14 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yc=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"}],["path",{d:"M16 4h2a2 2 0 0 1 2 2v4"}],["path",{d:"M21 14H11"}],["path",{d:"m15 10-4 4 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kc=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M10.42 12.61a2.1 2.1 0 1 1 2.97 2.97L7.95 21 4 22l.99-3.95 5.43-5.44Z"}],["path",{d:"M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5.5"}],["path",{d:"M4 13.5V6a2 2 0 0 1 2-2h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jc=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"}],["path",{d:"M12 11h4"}],["path",{d:"M12 16h4"}],["path",{d:"M8 11h.01"}],["path",{d:"M8 16h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qc=["svg",o,[["path",{d:"M15 2H9a1 1 0 0 0-1 1v2c0 .6.4 1 1 1h6c.6 0 1-.4 1-1V3c0-.6-.4-1-1-1Z"}],["path",{d:"M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2M16 4h2a2 2 0 0 1 2 2v2M11 14h10"}],["path",{d:"m17 10 4 4-4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tl=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-.5"}],["path",{d:"M16 4h2a2 2 0 0 1 1.73 1"}],["path",{d:"M18.42 9.61a2.1 2.1 0 1 1 2.97 2.97L16.95 17 13 18l.99-3.95 4.43-4.44Z"}],["path",{d:"M8 18h1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const el=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"}],["path",{d:"M9 12v-1h6v1"}],["path",{d:"M11 17h2"}],["path",{d:"M12 11v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sl=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"}],["path",{d:"m15 11-6 6"}],["path",{d:"m9 11 6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const al=["svg",o,[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",ry:"1"}],["path",{d:"M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const il=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 14.5 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 8 10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ol=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 9.5 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 16 10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 16.5 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ll=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 16 14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 14.5 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 12 16.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 9.5 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ul=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 8 14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 7.5 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polyline",{points:"12 6 12 12 16 14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xl=["svg",o,[["circle",{cx:"12",cy:"17",r:"3"}],["path",{d:"M4.2 15.1A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.2"}],["path",{d:"m15.7 18.4-.9-.3"}],["path",{d:"m9.2 15.9-.9-.3"}],["path",{d:"m10.6 20.7.3-.9"}],["path",{d:"m13.1 14.2.3-.9"}],["path",{d:"m13.6 20.7-.4-1"}],["path",{d:"m10.8 14.3-.4-1"}],["path",{d:"m8.3 18.6 1-.4"}],["path",{d:"m14.7 15.8 1-.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ml=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"M8 19v1"}],["path",{d:"M8 14v1"}],["path",{d:"M16 19v1"}],["path",{d:"M16 14v1"}],["path",{d:"M12 21v1"}],["path",{d:"M12 16v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ml=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"M16 17H7"}],["path",{d:"M17 21H9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yl=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"M16 14v2"}],["path",{d:"M8 14v2"}],["path",{d:"M16 20h.01"}],["path",{d:"M8 20h.01"}],["path",{d:"M12 16v2"}],["path",{d:"M12 22h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bl=["svg",o,[["path",{d:"M6 16.326A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 .5 8.973"}],["path",{d:"m13 12-3 5h4l-3 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wl=["svg",o,[["path",{d:"M10.083 9A6.002 6.002 0 0 1 16 4a4.243 4.243 0 0 0 6 6c0 2.22-1.206 4.16-3 5.197"}],["path",{d:"M3 20a5 5 0 1 1 8.9-4H13a3 3 0 0 1 2 5.24"}],["path",{d:"M11 20v2"}],["path",{d:"M7 19v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _l=["svg",o,[["path",{d:"M13 16a3 3 0 1 1 0 6H7a5 5 0 1 1 4.9-6Z"}],["path",{d:"M10.1 9A6 6 0 0 1 16 4a4.24 4.24 0 0 0 6 6 6 6 0 0 1-3 5.197"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kl=["svg",o,[["path",{d:"m2 2 20 20"}],["path",{d:"M5.782 5.782A7 7 0 0 0 9 19h8.5a4.5 4.5 0 0 0 1.307-.193"}],["path",{d:"M21.532 16.5A4.5 4.5 0 0 0 17.5 10h-1.79A7.008 7.008 0 0 0 10 5.07"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cl=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"m9.2 22 3-7"}],["path",{d:"m9 13-3 7"}],["path",{d:"m17 13-3 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sl=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"M16 14v6"}],["path",{d:"M8 14v6"}],["path",{d:"M12 16v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ll=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"M8 15h.01"}],["path",{d:"M8 19h.01"}],["path",{d:"M12 17h.01"}],["path",{d:"M12 21h.01"}],["path",{d:"M16 15h.01"}],["path",{d:"M16 19h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Al=["svg",o,[["path",{d:"M12 2v2"}],["path",{d:"m4.93 4.93 1.41 1.41"}],["path",{d:"M20 12h2"}],["path",{d:"m19.07 4.93-1.41 1.41"}],["path",{d:"M15.947 12.65a4 4 0 0 0-5.925-4.128"}],["path",{d:"M3 20a5 5 0 1 1 8.9-4H13a3 3 0 0 1 2 5.24"}],["path",{d:"M11 20v2"}],["path",{d:"M7 19v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hl=["svg",o,[["path",{d:"M12 2v2"}],["path",{d:"m4.93 4.93 1.41 1.41"}],["path",{d:"M20 12h2"}],["path",{d:"m19.07 4.93-1.41 1.41"}],["path",{d:"M15.947 12.65a4 4 0 0 0-5.925-4.128"}],["path",{d:"M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vl=["svg",o,[["path",{d:"M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pl=["svg",o,[["path",{d:"M17.5 21H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"}],["path",{d:"M22 10a3 3 0 0 0-3-3h-2.207a5.502 5.502 0 0 0-10.702.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dl=["svg",o,[["path",{d:"M16.2 3.8a2.7 2.7 0 0 0-3.81 0l-.4.38-.4-.4a2.7 2.7 0 0 0-3.82 0C6.73 4.85 6.67 6.64 8 8l4 4 4-4c1.33-1.36 1.27-3.15.2-4.2z"}],["path",{d:"M8 8c-1.36-1.33-3.15-1.27-4.2-.2a2.7 2.7 0 0 0 0 3.81l.38.4-.4.4a2.7 2.7 0 0 0 0 3.82C4.85 17.27 6.64 17.33 8 16"}],["path",{d:"M16 16c1.36 1.33 3.15 1.27 4.2.2a2.7 2.7 0 0 0 0-3.81l-.38-.4.4-.4a2.7 2.7 0 0 0 0-3.82C19.15 6.73 17.36 6.67 16 8"}],["path",{d:"M7.8 20.2a2.7 2.7 0 0 0 3.81 0l.4-.38.4.4a2.7 2.7 0 0 0 3.82 0c1.06-1.06 1.12-2.85-.21-4.21l-4-4-4 4c-1.33 1.36-1.27 3.15-.2 4.2z"}],["path",{d:"m7 17-5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fl=["svg",o,[["path",{d:"M17.28 9.05a5.5 5.5 0 1 0-10.56 0A5.5 5.5 0 1 0 12 17.66a5.5 5.5 0 1 0 5.28-8.6Z"}],["path",{d:"M12 17.66L12 22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tl=["svg",o,[["path",{d:"m18 16 4-4-4-4"}],["path",{d:"m6 8-4 4 4 4"}],["path",{d:"m14.5 4-5 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bl=["svg",o,[["polyline",{points:"16 18 22 12 16 6"}],["polyline",{points:"8 6 2 12 8 18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ol=["svg",o,[["polygon",{points:"12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"}],["line",{x1:"12",x2:"12",y1:"22",y2:"15.5"}],["polyline",{points:"22 8.5 12 15.5 2 8.5"}],["polyline",{points:"2 15.5 12 8.5 22 15.5"}],["line",{x1:"12",x2:"12",y1:"2",y2:"8.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const El=["svg",o,[["path",{d:"M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"}],["polyline",{points:"7.5 4.21 12 6.81 16.5 4.21"}],["polyline",{points:"7.5 19.79 7.5 14.6 3 12"}],["polyline",{points:"21 12 16.5 14.6 16.5 19.79"}],["polyline",{points:"3.27 6.96 12 12.01 20.73 6.96"}],["line",{x1:"12",x2:"12",y1:"22.08",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rl=["svg",o,[["path",{d:"M17 8h1a4 4 0 1 1 0 8h-1"}],["path",{d:"M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"}],["line",{x1:"6",x2:"6",y1:"2",y2:"4"}],["line",{x1:"10",x2:"10",y1:"2",y2:"4"}],["line",{x1:"14",x2:"14",y1:"2",y2:"4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zl=["svg",o,[["path",{d:"M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z"}],["path",{d:"M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"}],["path",{d:"M12 2v2"}],["path",{d:"M12 22v-2"}],["path",{d:"m17 20.66-1-1.73"}],["path",{d:"M11 10.27 7 3.34"}],["path",{d:"m20.66 17-1.73-1"}],["path",{d:"m3.34 7 1.73 1"}],["path",{d:"M14 12h8"}],["path",{d:"M2 12h2"}],["path",{d:"m20.66 7-1.73 1"}],["path",{d:"m3.34 17 1.73-1"}],["path",{d:"m17 3.34-1 1.73"}],["path",{d:"m11 13.73-4 6.93"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Il=["svg",o,[["circle",{cx:"8",cy:"8",r:"6"}],["path",{d:"M18.09 10.37A6 6 0 1 1 10.34 18"}],["path",{d:"M7 6h1v4"}],["path",{d:"m16.71 13.88.7.71-2.82 2.82"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $l=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"12",x2:"12",y1:"3",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zl=["svg",o,[["rect",{width:"8",height:"8",x:"2",y:"2",rx:"2"}],["path",{d:"M14 2c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2"}],["path",{d:"M20 2c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2"}],["path",{d:"M10 18H5c-1.7 0-3-1.3-3-3v-1"}],["polyline",{points:"7 21 10 18 7 15"}],["rect",{width:"8",height:"8",x:"14",y:"14",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wl=["svg",o,[["path",{d:"M15 6v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nl=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polygon",{points:"16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jl=["svg",o,[["path",{d:"M5.5 8.5 9 12l-3.5 3.5L2 12l3.5-3.5Z"}],["path",{d:"m12 2 3.5 3.5L12 9 8.5 5.5 12 2Z"}],["path",{d:"M18.5 8.5 22 12l-3.5 3.5L15 12l3.5-3.5Z"}],["path",{d:"m12 15 3.5 3.5L12 22l-3.5-3.5L12 15Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ul=["svg",o,[["rect",{width:"14",height:"8",x:"5",y:"2",rx:"2"}],["rect",{width:"20",height:"8",x:"2",y:"14",rx:"2"}],["path",{d:"M6 18h2"}],["path",{d:"M12 18h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ql=["svg",o,[["path",{d:"M2 18a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v2H2v-2Z"}],["path",{d:"M20 16a8 8 0 1 0-16 0"}],["path",{d:"M12 4v4"}],["path",{d:"M10 4h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gl=["svg",o,[["path",{d:"m20.9 18.55-8-15.98a1 1 0 0 0-1.8 0l-8 15.98"}],["ellipse",{cx:"12",cy:"19",rx:"9",ry:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xl=["svg",o,[["rect",{x:"2",y:"6",width:"20",height:"8",rx:"1"}],["path",{d:"M17 14v7"}],["path",{d:"M7 14v7"}],["path",{d:"M17 3v3"}],["path",{d:"M7 3v3"}],["path",{d:"M10 14 2.3 6.3"}],["path",{d:"m14 6 7.7 7.7"}],["path",{d:"m8 6 8 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yl=["svg",o,[["path",{d:"M16 18a4 4 0 0 0-8 0"}],["circle",{cx:"12",cy:"11",r:"3"}],["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2"}],["line",{x1:"8",x2:"8",y1:"2",y2:"4"}],["line",{x1:"16",x2:"16",y1:"2",y2:"4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kl=["svg",o,[["path",{d:"M17 18a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2"}],["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2"}],["circle",{cx:"12",cy:"10",r:"2"}],["line",{x1:"8",x2:"8",y1:"2",y2:"4"}],["line",{x1:"16",x2:"16",y1:"2",y2:"4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jl=["svg",o,[["path",{d:"M22 7.7c0-.6-.4-1.2-.8-1.5l-6.3-3.9a1.72 1.72 0 0 0-1.7 0l-10.3 6c-.5.2-.9.8-.9 1.4v6.6c0 .5.4 1.2.8 1.5l6.3 3.9a1.72 1.72 0 0 0 1.7 0l10.3-6c.5-.3.9-1 .9-1.5Z"}],["path",{d:"M10 21.9V14L2.1 9.1"}],["path",{d:"m10 14 11.9-6.9"}],["path",{d:"M14 19.8v-8.1"}],["path",{d:"M18 17.5V9.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ql=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 18a6 6 0 0 0 0-12v12z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const td=["svg",o,[["path",{d:"M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"}],["path",{d:"M8.5 8.5v.01"}],["path",{d:"M16 15.5v.01"}],["path",{d:"M12 12v.01"}],["path",{d:"M11 17v.01"}],["path",{d:"M7 14v.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ed=["svg",o,[["path",{d:"m12 15 2 2 4-4"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sd=["svg",o,[["line",{x1:"12",x2:"18",y1:"15",y2:"15"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ad=["svg",o,[["line",{x1:"15",x2:"15",y1:"12",y2:"18"}],["line",{x1:"12",x2:"18",y1:"15",y2:"15"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const id=["svg",o,[["line",{x1:"12",x2:"18",y1:"18",y2:"12"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nd=["svg",o,[["line",{x1:"12",x2:"18",y1:"12",y2:"18"}],["line",{x1:"12",x2:"18",y1:"18",y2:"12"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const od=["svg",o,[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rd=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.17 14.83a4 4 0 1 0 0-5.66"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hd=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M14.83 14.83a4 4 0 1 1 0-5.66"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cd=["svg",o,[["polyline",{points:"9 10 4 15 9 20"}],["path",{d:"M20 4v7a4 4 0 0 1-4 4H4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ld=["svg",o,[["polyline",{points:"15 10 20 15 15 20"}],["path",{d:"M4 4v7a4 4 0 0 0 4 4h12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dd=["svg",o,[["polyline",{points:"14 15 9 20 4 15"}],["path",{d:"M20 4h-7a4 4 0 0 0-4 4v12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pd=["svg",o,[["polyline",{points:"14 9 9 4 4 9"}],["path",{d:"M20 20h-7a4 4 0 0 1-4-4V4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gd=["svg",o,[["polyline",{points:"10 15 15 20 20 15"}],["path",{d:"M4 4h7a4 4 0 0 1 4 4v12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ud=["svg",o,[["polyline",{points:"10 9 15 4 20 9"}],["path",{d:"M4 20h7a4 4 0 0 0 4-4V4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fd=["svg",o,[["polyline",{points:"9 14 4 9 9 4"}],["path",{d:"M20 20v-7a4 4 0 0 0-4-4H4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vd=["svg",o,[["polyline",{points:"15 14 20 9 15 4"}],["path",{d:"M4 20v-7a4 4 0 0 1 4-4h12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xd=["svg",o,[["rect",{x:"4",y:"4",width:"16",height:"16",rx:"2"}],["rect",{x:"9",y:"9",width:"6",height:"6"}],["path",{d:"M15 2v2"}],["path",{d:"M15 20v2"}],["path",{d:"M2 15h2"}],["path",{d:"M2 9h2"}],["path",{d:"M20 15h2"}],["path",{d:"M20 9h2"}],["path",{d:"M9 2v2"}],["path",{d:"M9 20v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const md=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M10 9.3a2.8 2.8 0 0 0-3.5 1 3.1 3.1 0 0 0 0 3.4 2.7 2.7 0 0 0 3.5 1"}],["path",{d:"M17 9.3a2.8 2.8 0 0 0-3.5 1 3.1 3.1 0 0 0 0 3.4 2.7 2.7 0 0 0 3.5 1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Md=["svg",o,[["rect",{width:"20",height:"14",x:"2",y:"5",rx:"2"}],["line",{x1:"2",x2:"22",y1:"10",y2:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yd=["svg",o,[["path",{d:"m4.6 13.11 5.79-3.21c1.89-1.05 4.79 1.78 3.71 3.71l-3.22 5.81C8.8 23.16.79 15.23 4.6 13.11Z"}],["path",{d:"m10.5 9.5-1-2.29C9.2 6.48 8.8 6 8 6H4.5C2.79 6 2 6.5 2 8.5a7.71 7.71 0 0 0 2 4.83"}],["path",{d:"M8 6c0-1.55.24-4-2-4-2 0-2.5 2.17-2.5 4"}],["path",{d:"m14.5 13.5 2.29 1c.73.3 1.21.7 1.21 1.5v3.5c0 1.71-.5 2.5-2.5 2.5a7.71 7.71 0 0 1-4.83-2"}],["path",{d:"M18 16c1.55 0 4-.24 4 2 0 2-2.17 2.5-4 2.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bd=["svg",o,[["path",{d:"M6 2v14a2 2 0 0 0 2 2h14"}],["path",{d:"M18 22V8a2 2 0 0 0-2-2H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wd=["svg",o,[["path",{d:"M11 2a2 2 0 0 0-2 2v5H4a2 2 0 0 0-2 2v2c0 1.1.9 2 2 2h5v5c0 1.1.9 2 2 2h2a2 2 0 0 0 2-2v-5h5a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2h-5V4a2 2 0 0 0-2-2h-2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _d=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"22",x2:"18",y1:"12",y2:"12"}],["line",{x1:"6",x2:"2",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"6",y2:"2"}],["line",{x1:"12",x2:"12",y1:"22",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kd=["svg",o,[["path",{d:"m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cd=["svg",o,[["path",{d:"m21.12 6.4-6.05-4.06a2 2 0 0 0-2.17-.05L2.95 8.41a2 2 0 0 0-.95 1.7v5.82a2 2 0 0 0 .88 1.66l6.05 4.07a2 2 0 0 0 2.17.05l9.95-6.12a2 2 0 0 0 .95-1.7V8.06a2 2 0 0 0-.88-1.66Z"}],["path",{d:"M10 22v-8L2.25 9.15"}],["path",{d:"m10 14 11.77-6.87"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sd=["svg",o,[["path",{d:"m6 8 1.75 12.28a2 2 0 0 0 2 1.72h4.54a2 2 0 0 0 2-1.72L18 8"}],["path",{d:"M5 8h14"}],["path",{d:"M7 15a6.47 6.47 0 0 1 5 0 6.47 6.47 0 0 0 5 0"}],["path",{d:"m12 8 1-6h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ld=["svg",o,[["circle",{cx:"12",cy:"12",r:"8"}],["line",{x1:"3",x2:"6",y1:"3",y2:"6"}],["line",{x1:"21",x2:"18",y1:"3",y2:"6"}],["line",{x1:"3",x2:"6",y1:"21",y2:"18"}],["line",{x1:"21",x2:"18",y1:"21",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ad=["svg",o,[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5v14a9 3 0 0 0 18 0V5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hd=["svg",o,[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 12a9 3 0 0 0 5 2.69"}],["path",{d:"M21 9.3V5"}],["path",{d:"M3 5v14a9 3 0 0 0 6.47 2.88"}],["path",{d:"M12 12v4h4"}],["path",{d:"M13 20a5 5 0 0 0 9-3 4.5 4.5 0 0 0-4.5-4.5c-1.33 0-2.54.54-3.41 1.41L12 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vd=["svg",o,[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 15 21.84"}],["path",{d:"M21 5V8"}],["path",{d:"M21 12L18 17H22L19 22"}],["path",{d:"M3 12A9 3 0 0 0 14.59 14.87"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pd=["svg",o,[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dd=["svg",o,[["path",{d:"M20 5H9l-7 7 7 7h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2Z"}],["line",{x1:"18",x2:"12",y1:"9",y2:"15"}],["line",{x1:"12",x2:"18",y1:"9",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fd=["svg",o,[["circle",{cx:"12",cy:"4",r:"2"}],["path",{d:"M10.2 3.2C5.5 4 2 8.1 2 13a2 2 0 0 0 4 0v-1a2 2 0 0 1 4 0v4a2 2 0 0 0 4 0v-4a2 2 0 0 1 4 0v1a2 2 0 0 0 4 0c0-4.9-3.5-9-8.2-9.8"}],["path",{d:"M3.2 14.8a9 9 0 0 0 17.6 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Td=["svg",o,[["circle",{cx:"19",cy:"19",r:"2"}],["circle",{cx:"5",cy:"5",r:"2"}],["path",{d:"M6.48 3.66a10 10 0 0 1 13.86 13.86"}],["path",{d:"m6.41 6.41 11.18 11.18"}],["path",{d:"M3.66 6.48a10 10 0 0 0 13.86 13.86"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bd=["svg",o,[["path",{d:"M2.7 10.3a2.41 2.41 0 0 0 0 3.41l7.59 7.59a2.41 2.41 0 0 0 3.41 0l7.59-7.59a2.41 2.41 0 0 0 0-3.41l-7.59-7.59a2.41 2.41 0 0 0-3.41 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Od=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M12 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ed=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M15 9h.01"}],["path",{d:"M9 15h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rd=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M16 8h.01"}],["path",{d:"M12 12h.01"}],["path",{d:"M8 16h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zd=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M16 8h.01"}],["path",{d:"M8 8h.01"}],["path",{d:"M8 16h.01"}],["path",{d:"M16 16h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Id=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M16 8h.01"}],["path",{d:"M8 8h.01"}],["path",{d:"M8 16h.01"}],["path",{d:"M16 16h.01"}],["path",{d:"M12 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $d=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M16 8h.01"}],["path",{d:"M16 12h.01"}],["path",{d:"M16 16h.01"}],["path",{d:"M8 8h.01"}],["path",{d:"M8 12h.01"}],["path",{d:"M8 16h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zd=["svg",o,[["rect",{width:"12",height:"12",x:"2",y:"10",rx:"2",ry:"2"}],["path",{d:"m17.92 14 3.5-3.5a2.24 2.24 0 0 0 0-3l-5-4.92a2.24 2.24 0 0 0-3 0L10 6"}],["path",{d:"M6 18h.01"}],["path",{d:"M10 14h.01"}],["path",{d:"M15 6h.01"}],["path",{d:"M18 9h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wd=["svg",o,[["path",{d:"M12 3v14"}],["path",{d:"M5 10h14"}],["path",{d:"M5 21h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nd=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["circle",{cx:"12",cy:"12",r:"4"}],["path",{d:"M12 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jd=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M6 12c0-1.7.7-3.2 1.8-4.2"}],["circle",{cx:"12",cy:"12",r:"2"}],["path",{d:"M18 12c0 1.7-.7 3.2-1.8 4.2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ud=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["circle",{cx:"12",cy:"12",r:"5"}],["path",{d:"M12 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qd=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["circle",{cx:"12",cy:"12",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gd=["svg",o,[["line",{x1:"8",x2:"16",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"16",y2:"16"}],["line",{x1:"12",x2:"12",y1:"8",y2:"8"}],["circle",{cx:"12",cy:"12",r:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xd=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"8",x2:"16",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"16",y2:"16"}],["line",{x1:"12",x2:"12",y1:"8",y2:"8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yd=["svg",o,[["circle",{cx:"12",cy:"6",r:"1"}],["line",{x1:"5",x2:"19",y1:"12",y2:"12"}],["circle",{cx:"12",cy:"18",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kd=["svg",o,[["path",{d:"M15 2c-1.35 1.5-2.092 3-2.5 4.5M9 22c1.35-1.5 2.092-3 2.5-4.5"}],["path",{d:"M2 15c3.333-3 6.667-3 10-3m10-3c-1.5 1.35-3 2.092-4.5 2.5"}],["path",{d:"m17 6-2.5-2.5"}],["path",{d:"m14 8-1.5-1.5"}],["path",{d:"m7 18 2.5 2.5"}],["path",{d:"m3.5 14.5.5.5"}],["path",{d:"m20 9 .5.5"}],["path",{d:"m6.5 12.5 1 1"}],["path",{d:"m16.5 10.5 1 1"}],["path",{d:"m10 16 1.5 1.5"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jd=["svg",o,[["path",{d:"M2 15c6.667-6 13.333 0 20-6"}],["path",{d:"M9 22c1.798-1.998 2.518-3.995 2.807-5.993"}],["path",{d:"M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"}],["path",{d:"m17 6-2.5-2.5"}],["path",{d:"m14 8-1-1"}],["path",{d:"m7 18 2.5 2.5"}],["path",{d:"m3.5 14.5.5.5"}],["path",{d:"m20 9 .5.5"}],["path",{d:"m6.5 12.5 1 1"}],["path",{d:"m16.5 10.5 1 1"}],["path",{d:"m10 16 1.5 1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qd=["svg",o,[["path",{d:"M10 5.172C10 3.782 8.423 2.679 6.5 3c-2.823.47-4.113 6.006-4 7 .08.703 1.725 1.722 3.656 1 1.261-.472 1.96-1.45 2.344-2.5"}],["path",{d:"M14.267 5.172c0-1.39 1.577-2.493 3.5-2.172 2.823.47 4.113 6.006 4 7-.08.703-1.725 1.722-3.656 1-1.261-.472-1.855-1.45-2.239-2.5"}],["path",{d:"M8 14v.5"}],["path",{d:"M16 14v.5"}],["path",{d:"M11.25 16.25h1.5L12 17l-.75-.75Z"}],["path",{d:"M4.42 11.247A13.152 13.152 0 0 0 4 14.556C4 18.728 7.582 21 12 21s8-2.272 8-6.444c0-1.061-.162-2.2-.493-3.309m-9.243-6.082A8.801 8.801 0 0 1 12 5c.78 0 1.5.108 2.161.306"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tp=["svg",o,[["line",{x1:"12",x2:"12",y1:"2",y2:"22"}],["path",{d:"M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ep=["svg",o,[["path",{d:"M20.5 10a2.5 2.5 0 0 1-2.4-3H18a2.95 2.95 0 0 1-2.6-4.4 10 10 0 1 0 6.3 7.1c-.3.2-.8.3-1.2.3"}],["circle",{cx:"12",cy:"12",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sp=["svg",o,[["path",{d:"M18 20V6a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v14"}],["path",{d:"M2 20h20"}],["path",{d:"M14 12v.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ap=["svg",o,[["path",{d:"M13 4h3a2 2 0 0 1 2 2v14"}],["path",{d:"M2 20h3"}],["path",{d:"M13 20h9"}],["path",{d:"M10 12v.01"}],["path",{d:"M13 4.562v16.157a1 1 0 0 1-1.242.97L5 20V5.562a2 2 0 0 1 1.515-1.94l4-1A2 2 0 0 1 13 4.561Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ip=["svg",o,[["circle",{cx:"12.1",cy:"12.1",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const np=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"M12 12v9"}],["path",{d:"m8 17 4 4 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const op=["svg",o,[["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["polyline",{points:"7 10 12 15 17 10"}],["line",{x1:"12",x2:"12",y1:"15",y2:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rp=["svg",o,[["circle",{cx:"12",cy:"5",r:"2"}],["path",{d:"m3 21 8.02-14.26"}],["path",{d:"m12.99 6.74 1.93 3.44"}],["path",{d:"M19 12c-3.87 4-10.13 4-14 0"}],["path",{d:"m21 21-2.16-3.84"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hp=["svg",o,[["path",{d:"M10 11h.01"}],["path",{d:"M14 6h.01"}],["path",{d:"M18 6h.01"}],["path",{d:"M6.5 13.1h.01"}],["path",{d:"M22 5c0 9-4 12-6 12s-6-3-6-12c0-2 2-3 6-3s6 1 6 3"}],["path",{d:"M17.4 9.9c-.8.8-2 .8-2.8 0"}],["path",{d:"M10.1 7.1C9 7.2 7.7 7.7 6 8.6c-3.5 2-4.7 3.9-3.7 5.6 4.5 7.8 9.5 8.4 11.2 7.4.9-.5 1.9-2.1 1.9-4.7"}],["path",{d:"M9.1 16.5c.3-1.1 1.4-1.7 2.4-1.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cp=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M19.13 5.09C15.22 9.14 10 10.44 2.25 10.94"}],["path",{d:"M21.75 12.84c-6.62-1.41-12.14 1-16.38 6.32"}],["path",{d:"M8.56 2.75c4.37 6 6 9.42 8 17.72"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lp=["svg",o,[["path",{d:"M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dp=["svg",o,[["path",{d:"M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z"}],["path",{d:"M12.56 6.6A10.97 10.97 0 0 0 14 3.02c.5 2.5 2 4.9 4 6.5s3 3.5 3 5.5a6.98 6.98 0 0 1-11.91 4.97"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pp=["svg",o,[["path",{d:"m2 2 8 8"}],["path",{d:"m22 2-8 8"}],["ellipse",{cx:"12",cy:"9",rx:"10",ry:"5"}],["path",{d:"M7 13.4v7.9"}],["path",{d:"M12 14v8"}],["path",{d:"M17 13.4v7.9"}],["path",{d:"M2 9v8a10 5 0 0 0 20 0V9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gp=["svg",o,[["path",{d:"M15.45 15.4c-2.13.65-4.3.32-5.7-1.1-2.29-2.27-1.76-6.5 1.17-9.42 2.93-2.93 7.15-3.46 9.43-1.18 1.41 1.41 1.74 3.57 1.1 5.71-1.4-.51-3.26-.02-4.64 1.36-1.38 1.38-1.87 3.23-1.36 4.63z"}],["path",{d:"m11.25 15.6-2.16 2.16a2.5 2.5 0 1 1-4.56 1.73 2.49 2.49 0 0 1-1.41-4.24 2.5 2.5 0 0 1 3.14-.32l2.16-2.16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const up=["svg",o,[["path",{d:"m6.5 6.5 11 11"}],["path",{d:"m21 21-1-1"}],["path",{d:"m3 3 1 1"}],["path",{d:"m18 22 4-4"}],["path",{d:"m2 6 4-4"}],["path",{d:"m3 10 7-7"}],["path",{d:"m14 21 7-7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fp=["svg",o,[["path",{d:"M6 18.5a3.5 3.5 0 1 0 7 0c0-1.57.92-2.52 2.04-3.46"}],["path",{d:"M6 8.5c0-.75.13-1.47.36-2.14"}],["path",{d:"M8.8 3.15A6.5 6.5 0 0 1 19 8.5c0 1.63-.44 2.81-1.09 3.76"}],["path",{d:"M12.5 6A2.5 2.5 0 0 1 15 8.5M10 13a2 2 0 0 0 1.82-1.18"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vp=["svg",o,[["path",{d:"M6 8.5a6.5 6.5 0 1 1 13 0c0 6-6 6-6 10a3.5 3.5 0 1 1-7 0"}],["path",{d:"M15 8.5a2.5 2.5 0 0 0-5 0v1a2 2 0 1 1 0 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xp=["svg",o,[["circle",{cx:"11.5",cy:"12.5",r:"3.5"}],["path",{d:"M3 8c0-3.5 2.5-6 6.5-6 5 0 4.83 3 7.5 5s5 2 5 6c0 4.5-2.5 6.5-7 6.5-2.5 0-2.5 2.5-6 2.5s-7-2-7-5.5c0-3 1.5-3 1.5-5C3.5 10 3 9 3 8Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mp=["svg",o,[["path",{d:"M6.399 6.399C5.362 8.157 4.65 10.189 4.5 12c-.37 4.43 1.27 9.95 7.5 10 3.256-.026 5.259-1.547 6.375-3.625"}],["path",{d:"M19.532 13.875A14.07 14.07 0 0 0 19.5 12c-.36-4.34-3.95-9.96-7.5-10-1.04.012-2.082.502-3.046 1.297"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mp=["svg",o,[["path",{d:"M12 22c6.23-.05 7.87-5.57 7.5-10-.36-4.34-3.95-9.96-7.5-10-3.55.04-7.14 5.66-7.5 10-.37 4.43 1.27 9.95 7.5 10z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yp=["svg",o,[["line",{x1:"5",x2:"19",y1:"9",y2:"9"}],["line",{x1:"5",x2:"19",y1:"15",y2:"15"}],["line",{x1:"19",x2:"5",y1:"5",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bp=["svg",o,[["line",{x1:"5",x2:"19",y1:"9",y2:"9"}],["line",{x1:"5",x2:"19",y1:"15",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wp=["svg",o,[["path",{d:"m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"}],["path",{d:"M22 21H7"}],["path",{d:"m5 11 9 9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _p=["svg",o,[["path",{d:"M4 10h12"}],["path",{d:"M4 14h9"}],["path",{d:"M19 6a7.7 7.7 0 0 0-5.2-2A7.9 7.9 0 0 0 6 12c0 4.4 3.5 8 7.8 8 2 0 3.8-.8 5.2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kp=["svg",o,[["path",{d:"m21 21-6-6m6 6v-4.8m0 4.8h-4.8"}],["path",{d:"M3 16.2V21m0 0h4.8M3 21l6-6"}],["path",{d:"M21 7.8V3m0 0h-4.8M21 3l-6 6"}],["path",{d:"M3 7.8V3m0 0h4.8M3 3l6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cp=["svg",o,[["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}],["polyline",{points:"15 3 21 3 21 9"}],["line",{x1:"10",x2:"21",y1:"14",y2:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sp=["svg",o,[["path",{d:"M9.88 9.88a3 3 0 1 0 4.24 4.24"}],["path",{d:"M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"}],["path",{d:"M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lp=["svg",o,[["path",{d:"M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"}],["circle",{cx:"12",cy:"12",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ap=["svg",o,[["path",{d:"M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hp=["svg",o,[["path",{d:"M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"}],["path",{d:"M17 18h1"}],["path",{d:"M12 18h1"}],["path",{d:"M7 18h1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vp=["svg",o,[["path",{d:"M10.827 16.379a6.082 6.082 0 0 1-8.618-7.002l5.412 1.45a6.082 6.082 0 0 1 7.002-8.618l-1.45 5.412a6.082 6.082 0 0 1 8.618 7.002l-5.412-1.45a6.082 6.082 0 0 1-7.002 8.618l1.45-5.412Z"}],["path",{d:"M12 12v.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pp=["svg",o,[["polygon",{points:"13 19 22 12 13 5 13 19"}],["polygon",{points:"2 19 11 12 2 5 2 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dp=["svg",o,[["path",{d:"M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"}],["line",{x1:"16",x2:"2",y1:"8",y2:"22"}],["line",{x1:"17.5",x2:"9",y1:"15",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fp=["svg",o,[["circle",{cx:"12",cy:"12",r:"2"}],["path",{d:"M12 2v4"}],["path",{d:"m6.8 15-3.5 2"}],["path",{d:"m20.7 7-3.5 2"}],["path",{d:"M6.8 9 3.3 7"}],["path",{d:"m20.7 17-3.5-2"}],["path",{d:"m9 22 3-8 3 8"}],["path",{d:"M8 22h8"}],["path",{d:"M18 18.7a9 9 0 1 0-12 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tp=["svg",o,[["path",{d:"M5 5.5A3.5 3.5 0 0 1 8.5 2H12v7H8.5A3.5 3.5 0 0 1 5 5.5z"}],["path",{d:"M12 2h3.5a3.5 3.5 0 1 1 0 7H12V2z"}],["path",{d:"M12 12.5a3.5 3.5 0 1 1 7 0 3.5 3.5 0 1 1-7 0z"}],["path",{d:"M5 19.5A3.5 3.5 0 0 1 8.5 16H12v3.5a3.5 3.5 0 1 1-7 0z"}],["path",{d:"M5 12.5A3.5 3.5 0 0 1 8.5 9H12v7H8.5A3.5 3.5 0 0 1 5 12.5z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bp=["svg",o,[["path",{d:"M4 22V4c0-.5.2-1 .6-1.4C5 2.2 5.5 2 6 2h8.5L20 7.5V20c0 .5-.2 1-.6 1.4-.4.4-.9.6-1.4.6h-2"}],["polyline",{points:"14 2 14 8 20 8"}],["circle",{cx:"10",cy:"20",r:"2"}],["path",{d:"M10 7V6"}],["path",{d:"M10 12v-1"}],["path",{d:"M10 18v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Op=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v2"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M2 17v-3a4 4 0 0 1 8 0v3"}],["circle",{cx:"9",cy:"17",r:"1"}],["circle",{cx:"3",cy:"17",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ep=["svg",o,[["path",{d:"M17.5 22h.5c.5 0 1-.2 1.4-.6.4-.4.6-.9.6-1.4V7.5L14.5 2H6c-.5 0-1 .2-1.4.6C4.2 3 4 3.5 4 4v3"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M10 20v-1a2 2 0 1 1 4 0v1a2 2 0 1 1-4 0Z"}],["path",{d:"M6 20v-1a2 2 0 1 0-4 0v1a2 2 0 1 0 4 0Z"}],["path",{d:"M2 19v-3a6 6 0 0 1 12 0v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Is=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M8 10v8h8"}],["path",{d:"m8 18 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rp=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["path",{d:"M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"}],["path",{d:"m14 12.5 1 5.5-3-1-3 1 1-5.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zp=["svg",o,[["path",{d:"M4 7V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2h-6"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M5 17a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"}],["path",{d:"M7 16.5 8 22l-3-1-3 1 1-5.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ip=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M12 18v-6"}],["path",{d:"M8 18v-1"}],["path",{d:"M16 18v-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $p=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M12 18v-4"}],["path",{d:"M8 18v-2"}],["path",{d:"M16 18v-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zp=["svg",o,[["path",{d:"M14.5 22H18a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M2.97 13.12c-.6.36-.97 1.02-.97 1.74v3.28c0 .72.37 1.38.97 1.74l3 1.83c.63.39 1.43.39 2.06 0l3-1.83c.6-.36.97-1.02.97-1.74v-3.28c0-.72-.37-1.38-.97-1.74l-3-1.83a1.97 1.97 0 0 0-2.06 0l-3 1.83Z"}],["path",{d:"m7 17-4.74-2.85"}],["path",{d:"m7 17 4.74-2.85"}],["path",{d:"M7 17v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wp=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m3 15 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Np=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m9 15 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jp=["svg",o,[["path",{d:"M16 22h2c.5 0 1-.2 1.4-.6.4-.4.6-.9.6-1.4V7.5L14.5 2H6c-.5 0-1 .2-1.4.6C4.2 3 4 3.5 4 4v3"}],["polyline",{points:"14 2 14 8 20 8"}],["circle",{cx:"8",cy:"16",r:"6"}],["path",{d:"M9.5 17.5 8 16.25V14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Up=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m9 18 3-3-3-3"}],["path",{d:"m5 12-3 3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qp=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m10 13-2 2 2 2"}],["path",{d:"m14 17 2-2-2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $s=["svg",o,[["circle",{cx:"6",cy:"13",r:"3"}],["path",{d:"m9.7 14.4-.9-.3"}],["path",{d:"m3.2 11.9-.9-.3"}],["path",{d:"m4.6 16.7.3-.9"}],["path",{d:"m7.6 16.7-.4-1"}],["path",{d:"m4.8 10.3-.4-1"}],["path",{d:"m2.3 14.6 1-.4"}],["path",{d:"m8.7 11.8 1-.4"}],["path",{d:"m7.4 9.3-.3.9"}],["path",{d:"M14 2v6h6"}],["path",{d:"M4 5.5V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2H6a2 2 0 0 1-2-1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gp=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["path",{d:"M12 13V7"}],["path",{d:"M9 10h6"}],["path",{d:"M9 17h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xp=["svg",o,[["rect",{width:"4",height:"6",x:"2",y:"12",rx:"2"}],["path",{d:"M14 2v6h6"}],["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["path",{d:"M10 12h2v6"}],["path",{d:"M10 18h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yp=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M12 18v-6"}],["path",{d:"m9 15 3 3 3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kp=["svg",o,[["path",{d:"M4 13.5V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2h-5.5"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M10.42 12.61a2.1 2.1 0 1 1 2.97 2.97L7.95 21 4 22l.99-3.95 5.43-5.44Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jp=["svg",o,[["path",{d:"M4 6V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2H4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M10.29 10.7a2.43 2.43 0 0 0-2.66-.52c-.29.12-.56.3-.78.53l-.35.34-.35-.34a2.43 2.43 0 0 0-2.65-.53c-.3.12-.56.3-.79.53-.95.94-1 2.53.2 3.74L6.5 18l3.6-3.55c1.2-1.21 1.14-2.8.19-3.74Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qp=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["circle",{cx:"10",cy:"13",r:"2"}],["path",{d:"m20 17-1.09-1.09a2 2 0 0 0-2.82 0L10 22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M2 15h10"}],["path",{d:"m9 18 3-3-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M4 12a1 1 0 0 0-1 1v1a1 1 0 0 1-1 1 1 1 0 0 1 1 1v1a1 1 0 0 0 1 1"}],["path",{d:"M8 18a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1 1 1 0 0 1-1-1v-1a1 1 0 0 0-1-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M10 12a1 1 0 0 0-1 1v1a1 1 0 0 1-1 1 1 1 0 0 1 1 1v1a1 1 0 0 0 1 1"}],["path",{d:"M14 18a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1 1 1 0 0 1-1-1v-1a1 1 0 0 0-1-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a4=["svg",o,[["path",{d:"M4 10V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2H4"}],["polyline",{points:"14 2 14 8 20 8"}],["circle",{cx:"4",cy:"16",r:"2"}],["path",{d:"m10 10-4.5 4.5"}],["path",{d:"m9 11 1 1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["circle",{cx:"10",cy:"16",r:"2"}],["path",{d:"m16 10-4.5 4.5"}],["path",{d:"m15 11 1 1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m16 13-3.5 3.5-2-2L8 17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o4=["svg",o,[["path",{d:"M4 5V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2H4"}],["polyline",{points:"14 2 14 8 20 8"}],["rect",{width:"8",height:"5",x:"2",y:"13",rx:"1"}],["path",{d:"M8 13v-2a2 2 0 1 0-4 0v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["rect",{width:"8",height:"6",x:"8",y:"12",rx:"1"}],["path",{d:"M15 12v-2a3 3 0 1 0-6 0v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M3 15h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["line",{x1:"9",x2:"15",y1:"15",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l4=["svg",o,[["circle",{cx:"14",cy:"16",r:"2"}],["circle",{cx:"6",cy:"18",r:"2"}],["path",{d:"M4 12.4V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2h-7.5"}],["path",{d:"M8 18v-7.7L16 9v7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M2 15h10"}],["path",{d:"m5 12-3 3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p4=["svg",o,[["path",{d:"M16 22h2a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v3"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M4.04 11.71a5.84 5.84 0 1 0 8.2 8.29"}],["path",{d:"M13.83 16A5.83 5.83 0 0 0 8 10.17V16h5.83Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M3 15h6"}],["path",{d:"M6 12v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["line",{x1:"12",x2:"12",y1:"18",y2:"12"}],["line",{x1:"9",x2:"15",y1:"15",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["path",{d:"M10 10.3c.2-.4.5-.8.9-1a2.1 2.1 0 0 1 2.6.4c.3.4.5.8.5 1.3 0 1.3-2 2-2 2"}],["path",{d:"M12 17h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v4=["svg",o,[["path",{d:"M20 10V7.5L14.5 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h4.5"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M16 22a2 2 0 0 1-2-2"}],["path",{d:"M20 22a2 2 0 0 0 2-2"}],["path",{d:"M20 14a2 2 0 0 1 2 2"}],["path",{d:"M16 14a2 2 0 0 0-2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["circle",{cx:"11.5",cy:"14.5",r:"2.5"}],["path",{d:"M13.25 16.25 15 18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v3"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M5 17a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"}],["path",{d:"m9 18-1.5-1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M4=["svg",o,[["path",{d:"M20 19.5v.5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8.5L18 5.5"}],["path",{d:"M8 18h1"}],["path",{d:"M18.42 9.61a2.1 2.1 0 1 1 2.97 2.97L16.95 17 13 18l.99-3.95 4.43-4.44Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M8 13h2"}],["path",{d:"M8 17h2"}],["path",{d:"M14 13h2"}],["path",{d:"M14 17h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b4=["svg",o,[["path",{d:"M16 2v5h5"}],["path",{d:"M21 6v6.5c0 .8-.7 1.5-1.5 1.5h-7c-.8 0-1.5-.7-1.5-1.5v-9c0-.8.7-1.5 1.5-1.5H17l4 4z"}],["path",{d:"M7 8v8.8c0 .3.2.6.4.8.2.2.5.4.8.4H15"}],["path",{d:"M3 12v8.8c0 .3.2.6.4.8.2.2.5.4.8.4H11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v7"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m10 18 3-3-3-3"}],["path",{d:"M4 18v-1a2 2 0 0 1 2-2h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m8 16 2-2-2-2"}],["path",{d:"M12 18h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["line",{x1:"16",x2:"8",y1:"13",y2:"13"}],["line",{x1:"16",x2:"8",y1:"17",y2:"17"}],["line",{x1:"10",x2:"8",y1:"9",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M2 13v-1h6v1"}],["path",{d:"M4 18h2"}],["path",{d:"M5 12v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M9 13v-1h6v1"}],["path",{d:"M11 18h2"}],["path",{d:"M12 12v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M12 12v6"}],["path",{d:"m15 15-3-3-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A4=["svg",o,[["path",{d:"M4 8V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2H4"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m10 15.5 4 2.5v-6l-4 2.5"}],["rect",{width:"8",height:"6",x:"2",y:"12",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m10 11 5 3-5 3v-6Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"M11.5 13.5c.32.4.5.94.5 1.5s-.18 1.1-.5 1.5"}],["path",{d:"M15 12c.64.8 1 1.87 1 3s-.36 2.2-1 3"}],["path",{d:"M8 15h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v3"}],["polyline",{points:"14 2 14 8 20 8"}],["path",{d:"m7 10-3 2H2v4h2l3 2v-8Z"}],["path",{d:"M11 11c.64.8 1 1.87 1 3s-.36 2.2-1 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F4=["svg",o,[["path",{d:"M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"}],["path",{d:"M14 2v6h6"}],["path",{d:"m3 12.5 5 5"}],["path",{d:"m8 12.5-5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}],["line",{x1:"9.5",x2:"14.5",y1:"12.5",y2:"17.5"}],["line",{x1:"14.5",x2:"9.5",y1:"12.5",y2:"17.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B4=["svg",o,[["path",{d:"M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"}],["polyline",{points:"14 2 14 8 20 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O4=["svg",o,[["path",{d:"M15.5 2H8.6c-.4 0-.8.2-1.1.5-.3.3-.5.7-.5 1.1v12.8c0 .4.2.8.5 1.1.3.3.7.5 1.1.5h9.8c.4 0 .8-.2 1.1-.5.3-.3.5-.7.5-1.1V6.5L15.5 2z"}],["path",{d:"M3 7.6v12.8c0 .4.2.8.5 1.1.3.3.7.5 1.1.5h9.8"}],["path",{d:"M15 2v5h5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E4=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M7 3v18"}],["path",{d:"M3 7.5h4"}],["path",{d:"M3 12h18"}],["path",{d:"M3 16.5h4"}],["path",{d:"M17 3v18"}],["path",{d:"M17 7.5h4"}],["path",{d:"M17 16.5h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R4=["svg",o,[["path",{d:"M13.013 3H2l8 9.46V19l4 2v-8.54l.9-1.055"}],["path",{d:"m22 3-5 5"}],["path",{d:"m17 3 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z4=["svg",o,[["polygon",{points:"22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I4=["svg",o,[["path",{d:"M2 12C2 6.5 6.5 2 12 2a10 10 0 0 1 8 4"}],["path",{d:"M5 19.5C5.5 18 6 15 6 12c0-.7.12-1.37.34-2"}],["path",{d:"M17.29 21.02c.12-.6.43-2.3.5-3.02"}],["path",{d:"M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"}],["path",{d:"M8.65 22c.21-.66.45-1.32.57-2"}],["path",{d:"M14 13.12c0 2.38 0 6.38-1 8.88"}],["path",{d:"M2 16h.01"}],["path",{d:"M21.8 16c.2-2 .131-5.354 0-6"}],["path",{d:"M9 6.8a6 6 0 0 1 9 5.2c0 .47 0 1.17-.02 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $4=["svg",o,[["path",{d:"M18 12.47v.03m0-.5v.47m-.475 5.056A6.744 6.744 0 0 1 15 18c-3.56 0-7.56-2.53-8.5-6 .348-1.28 1.114-2.433 2.121-3.38m3.444-2.088A8.802 8.802 0 0 1 15 6c3.56 0 6.06 2.54 7 6-.309 1.14-.786 2.177-1.413 3.058"}],["path",{d:"M7 10.67C7 8 5.58 5.97 2.73 5.5c-1 1.5-1 5 .23 6.5-1.24 1.5-1.24 5-.23 6.5C5.58 18.03 7 16 7 13.33m7.48-4.372A9.77 9.77 0 0 1 16 6.07m0 11.86a9.77 9.77 0 0 1-1.728-3.618"}],["path",{d:"m16.01 17.93-.23 1.4A2 2 0 0 1 13.8 21H9.5a5.96 5.96 0 0 0 1.49-3.98M8.53 3h5.27a2 2 0 0 1 1.98 1.67l.23 1.4M2 2l20 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z4=["svg",o,[["path",{d:"M2 16s9-15 20-4C11 23 2 8 2 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W4=["svg",o,[["path",{d:"M6.5 12c.94-3.46 4.94-6 8.5-6 3.56 0 6.06 2.54 7 6-.94 3.47-3.44 6-7 6s-7.56-2.53-8.5-6Z"}],["path",{d:"M18 12v.5"}],["path",{d:"M16 17.93a9.77 9.77 0 0 1 0-11.86"}],["path",{d:"M7 10.67C7 8 5.58 5.97 2.73 5.5c-1 1.5-1 5 .23 6.5-1.24 1.5-1.24 5-.23 6.5C5.58 18.03 7 16 7 13.33"}],["path",{d:"M10.46 7.26C10.2 5.88 9.17 4.24 8 3h5.8a2 2 0 0 1 1.98 1.67l.23 1.4"}],["path",{d:"m16.01 17.93-.23 1.4A2 2 0 0 1 13.8 21H9.5a5.96 5.96 0 0 0 1.49-3.98"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N4=["svg",o,[["path",{d:"M8 2c3 0 5 2 8 2s4-1 4-1v11"}],["path",{d:"M4 22V4"}],["path",{d:"M4 15s1-1 4-1 5 2 8 2"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j4=["svg",o,[["path",{d:"M17 22V2L7 7l10 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U4=["svg",o,[["path",{d:"M7 22V2l10 5-10 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q4=["svg",o,[["path",{d:"M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"}],["line",{x1:"4",x2:"4",y1:"22",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G4=["svg",o,[["path",{d:"M12 2c1 3 2.5 3.5 3.5 4.5A5 5 0 0 1 17 10a5 5 0 1 1-10 0c0-.3 0-.6.1-.9a2 2 0 1 0 3.3-2C8 4.5 11 2 12 2Z"}],["path",{d:"m5 22 14-4"}],["path",{d:"m5 18 14 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X4=["svg",o,[["path",{d:"M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y4=["svg",o,[["path",{d:"M16 16v4a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V10c0-2-2-2-2-4"}],["path",{d:"M7 2h11v4c0 2-2 2-2 4v1"}],["line",{x1:"11",x2:"18",y1:"6",y2:"6"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K4=["svg",o,[["path",{d:"M18 6c0 2-2 2-2 4v10a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V10c0-2-2-2-2-4V2h12z"}],["line",{x1:"6",x2:"18",y1:"6",y2:"6"}],["line",{x1:"12",x2:"12",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J4=["svg",o,[["path",{d:"M10 10 4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-1.272-2.542"}],["path",{d:"M10 2v2.343"}],["path",{d:"M14 2v6.343"}],["path",{d:"M8.5 2h7"}],["path",{d:"M7 16h9"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q4=["svg",o,[["path",{d:"M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"}],["path",{d:"M8.5 2h7"}],["path",{d:"M7 16h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t5=["svg",o,[["path",{d:"M10 2v7.31"}],["path",{d:"M14 9.3V1.99"}],["path",{d:"M8.5 2h7"}],["path",{d:"M14 9.3a6.5 6.5 0 1 1-4 0"}],["path",{d:"M5.52 16h12.96"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e5=["svg",o,[["path",{d:"m3 7 5 5-5 5V7"}],["path",{d:"m21 7-5 5 5 5V7"}],["path",{d:"M12 20v2"}],["path",{d:"M12 14v2"}],["path",{d:"M12 8v2"}],["path",{d:"M12 2v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s5=["svg",o,[["path",{d:"M8 3H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h3"}],["path",{d:"M16 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-3"}],["path",{d:"M12 20v2"}],["path",{d:"M12 14v2"}],["path",{d:"M12 8v2"}],["path",{d:"M12 2v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a5=["svg",o,[["path",{d:"m17 3-5 5-5-5h10"}],["path",{d:"m17 21-5-5-5 5h10"}],["path",{d:"M4 12H2"}],["path",{d:"M10 12H8"}],["path",{d:"M16 12h-2"}],["path",{d:"M22 12h-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i5=["svg",o,[["path",{d:"M21 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v3"}],["path",{d:"M21 16v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3"}],["path",{d:"M4 12H2"}],["path",{d:"M10 12H8"}],["path",{d:"M16 12h-2"}],["path",{d:"M22 12h-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n5=["svg",o,[["path",{d:"M12 5a3 3 0 1 1 3 3m-3-3a3 3 0 1 0-3 3m3-3v1M9 8a3 3 0 1 0 3 3M9 8h1m5 0a3 3 0 1 1-3 3m3-3h-1m-2 3v-1"}],["circle",{cx:"12",cy:"8",r:"2"}],["path",{d:"M12 10v12"}],["path",{d:"M12 22c4.2 0 7-1.667 7-5-4.2 0-7 1.667-7 5Z"}],["path",{d:"M12 22c-4.2 0-7-1.667-7-5 4.2 0 7 1.667 7 5Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o5=["svg",o,[["path",{d:"M12 7.5a4.5 4.5 0 1 1 4.5 4.5M12 7.5A4.5 4.5 0 1 0 7.5 12M12 7.5V9m-4.5 3a4.5 4.5 0 1 0 4.5 4.5M7.5 12H9m7.5 0a4.5 4.5 0 1 1-4.5 4.5m4.5-4.5H15m-3 4.5V15"}],["circle",{cx:"12",cy:"12",r:"3"}],["path",{d:"m8 16 1.5-1.5"}],["path",{d:"M14.5 9.5 16 8"}],["path",{d:"m8 8 1.5 1.5"}],["path",{d:"M14.5 14.5 16 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r5=["svg",o,[["circle",{cx:"12",cy:"12",r:"3"}],["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h5=["svg",o,[["path",{d:"M2 12h6"}],["path",{d:"M22 12h-6"}],["path",{d:"M12 2v2"}],["path",{d:"M12 8v2"}],["path",{d:"M12 14v2"}],["path",{d:"M12 20v2"}],["path",{d:"m19 9-3 3 3 3"}],["path",{d:"m5 15 3-3-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c5=["svg",o,[["path",{d:"M12 22v-6"}],["path",{d:"M12 8V2"}],["path",{d:"M4 12H2"}],["path",{d:"M10 12H8"}],["path",{d:"M16 12h-2"}],["path",{d:"M22 12h-2"}],["path",{d:"m15 19-3-3-3 3"}],["path",{d:"m15 5-3 3-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l5=["svg",o,[["circle",{cx:"15",cy:"19",r:"2"}],["path",{d:"M20.9 19.8A2 2 0 0 0 22 18V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h5.1"}],["path",{d:"M15 11v-1"}],["path",{d:"M15 17v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d5=["svg",o,[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}],["path",{d:"m9 13 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p5=["svg",o,[["circle",{cx:"16",cy:"16",r:"6"}],["path",{d:"M7 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2"}],["path",{d:"M16 14v2l1 1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g5=["svg",o,[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}],["path",{d:"M2 10h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zs=["svg",o,[["circle",{cx:"18",cy:"18",r:"3"}],["path",{d:"M10.3 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v3.3"}],["path",{d:"m21.7 19.4-.9-.3"}],["path",{d:"m15.2 16.9-.9-.3"}],["path",{d:"m16.6 21.7.3-.9"}],["path",{d:"m19.1 15.2.3-.9"}],["path",{d:"m19.6 21.7-.4-1"}],["path",{d:"m16.8 15.3-.4-1"}],["path",{d:"m14.3 19.6 1-.4"}],["path",{d:"m20.7 16.8 1-.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u5=["svg",o,[["path",{d:"M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"}],["circle",{cx:"12",cy:"13",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f5=["svg",o,[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}],["path",{d:"M12 10v6"}],["path",{d:"m15 13-3 3-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v5=["svg",o,[["path",{d:"M8.4 10.6a2.1 2.1 0 1 1 2.99 2.98L6 19l-4 1 1-3.9Z"}],["path",{d:"M2 11.5V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-9.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x5=["svg",o,[["path",{d:"M9 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v5"}],["circle",{cx:"13",cy:"12",r:"2"}],["path",{d:"M18 19c-2.8 0-5-2.2-5-5v8"}],["circle",{cx:"20",cy:"19",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m5=["svg",o,[["circle",{cx:"12",cy:"13",r:"2"}],["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}],["path",{d:"M14 13h3"}],["path",{d:"M7 13h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M5=["svg",o,[["path",{d:"M11 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v1.5"}],["path",{d:"M13.9 17.45c-1.2-1.2-1.14-2.8-.2-3.73a2.43 2.43 0 0 1 3.44 0l.36.34.34-.34a2.43 2.43 0 0 1 3.45-.01v0c.95.95 1 2.53-.2 3.74L17.5 21Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y5=["svg",o,[["path",{d:"M2 9V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-1"}],["path",{d:"M2 13h10"}],["path",{d:"m9 16 3-3-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b5=["svg",o,[["path",{d:"M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"}],["path",{d:"M8 10v4"}],["path",{d:"M12 10v2"}],["path",{d:"M16 10v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w5=["svg",o,[["circle",{cx:"16",cy:"20",r:"2"}],["path",{d:"M10 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v2"}],["path",{d:"m22 14-4.5 4.5"}],["path",{d:"m21 15 1 1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _5=["svg",o,[["rect",{width:"8",height:"5",x:"14",y:"17",rx:"1"}],["path",{d:"M10 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v2.5"}],["path",{d:"M20 17v-2a2 2 0 1 0-4 0v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k5=["svg",o,[["path",{d:"M9 13h6"}],["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C5=["svg",o,[["path",{d:"m6 14 1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H18a2 2 0 0 1 2 2v2"}],["circle",{cx:"14",cy:"15",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S5=["svg",o,[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L5=["svg",o,[["path",{d:"M2 7.5V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H20a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2"}],["path",{d:"M2 13h10"}],["path",{d:"m5 10-3 3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A5=["svg",o,[["path",{d:"M12 10v6"}],["path",{d:"M9 13h6"}],["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H5=["svg",o,[["path",{d:"M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"}],["circle",{cx:"12",cy:"13",r:"2"}],["path",{d:"M12 15v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V5=["svg",o,[["circle",{cx:"11.5",cy:"12.5",r:"2.5"}],["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}],["path",{d:"M13.3 14.3 15 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P5=["svg",o,[["circle",{cx:"17",cy:"17",r:"3"}],["path",{d:"M10.7 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v4.1"}],["path",{d:"m21 21-1.5-1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D5=["svg",o,[["path",{d:"M2 9V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H20a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2"}],["path",{d:"m8 16 3-3-3-3"}],["path",{d:"M2 16v-1a2 2 0 0 1 2-2h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F5=["svg",o,[["path",{d:"M9 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v1"}],["path",{d:"M12 10v4h4"}],["path",{d:"m12 14 1.5-1.5c.9-.9 2.2-1.5 3.5-1.5s2.6.6 3.5 1.5c.4.4.8 1 1 1.5"}],["path",{d:"M22 22v-4h-4"}],["path",{d:"m22 18-1.5 1.5c-.9.9-2.1 1.5-3.5 1.5s-2.6-.6-3.5-1.5c-.4-.4-.8-1-1-1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T5=["svg",o,[["path",{d:"M20 10a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2.5a1 1 0 0 1-.8-.4l-.9-1.2A1 1 0 0 0 15 3h-2a1 1 0 0 0-1 1v5a1 1 0 0 0 1 1Z"}],["path",{d:"M20 21a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1h-2.9a1 1 0 0 1-.88-.55l-.42-.85a1 1 0 0 0-.92-.6H13a1 1 0 0 0-1 1v5a1 1 0 0 0 1 1Z"}],["path",{d:"M3 5a2 2 0 0 0 2 2h3"}],["path",{d:"M3 3v13a2 2 0 0 0 2 2h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B5=["svg",o,[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}],["path",{d:"M12 10v6"}],["path",{d:"m9 13 3-3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O5=["svg",o,[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}],["path",{d:"m9.5 10.5 5 5"}],["path",{d:"m14.5 10.5-5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E5=["svg",o,[["path",{d:"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R5=["svg",o,[["path",{d:"M20 17a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3.9a2 2 0 0 1-1.69-.9l-.81-1.2a2 2 0 0 0-1.67-.9H8a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2Z"}],["path",{d:"M2 8v11a2 2 0 0 0 2 2h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z5=["svg",o,[["path",{d:"M4 16v-2.38C4 11.5 2.97 10.5 3 8c.03-2.72 1.49-6 4.5-6C9.37 2 10 3.8 10 5.5c0 3.11-2 5.66-2 8.68V16a2 2 0 1 1-4 0Z"}],["path",{d:"M20 20v-2.38c0-2.12 1.03-3.12 1-5.62-.03-2.72-1.49-6-4.5-6C14.63 6 14 7.8 14 9.5c0 3.11 2 5.66 2 8.68V20a2 2 0 1 0 4 0Z"}],["path",{d:"M16 17h4"}],["path",{d:"M4 13h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I5=["svg",o,[["path",{d:"M12 12H5a2 2 0 0 0-2 2v5"}],["circle",{cx:"13",cy:"19",r:"2"}],["circle",{cx:"5",cy:"19",r:"2"}],["path",{d:"M8 19h3m5-17v17h6M6 12V7c0-1.1.9-2 2-2h3l5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $5=["svg",o,[["rect",{width:"20",height:"12",x:"2",y:"6",rx:"2"}],["path",{d:"M12 12h.01"}],["path",{d:"M17 12h.01"}],["path",{d:"M7 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z5=["svg",o,[["polyline",{points:"15 17 20 12 15 7"}],["path",{d:"M4 18v-2a4 4 0 0 1 4-4h12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W5=["svg",o,[["line",{x1:"22",x2:"2",y1:"6",y2:"6"}],["line",{x1:"22",x2:"2",y1:"18",y2:"18"}],["line",{x1:"6",x2:"6",y1:"2",y2:"22"}],["line",{x1:"18",x2:"18",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N5=["svg",o,[["path",{d:"M5 16V9h14V2H5l14 14h-7m-7 0 7 7v-7m-7 0h7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j5=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M16 16s-1.5-2-4-2-4 2-4 2"}],["line",{x1:"9",x2:"9.01",y1:"9",y2:"9"}],["line",{x1:"15",x2:"15.01",y1:"9",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U5=["svg",o,[["line",{x1:"3",x2:"15",y1:"22",y2:"22"}],["line",{x1:"4",x2:"14",y1:"9",y2:"9"}],["path",{d:"M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18"}],["path",{d:"M14 13h2a2 2 0 0 1 2 2v2a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L18 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q5=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}],["rect",{width:"10",height:"8",x:"7",y:"8",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G5=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M9 17c2 0 2.8-1 2.8-2.8V10c0-2 1-3.3 3.2-3"}],["path",{d:"M9 11.2h5.7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X5=["svg",o,[["path",{d:"M2 7v10"}],["path",{d:"M6 5v14"}],["rect",{width:"12",height:"18",x:"10",y:"3",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y5=["svg",o,[["path",{d:"M2 3v18"}],["rect",{width:"12",height:"18",x:"6",y:"3",rx:"2"}],["path",{d:"M22 3v18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K5=["svg",o,[["rect",{width:"18",height:"14",x:"3",y:"3",rx:"2"}],["path",{d:"M4 21h1"}],["path",{d:"M9 21h1"}],["path",{d:"M14 21h1"}],["path",{d:"M19 21h1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J5=["svg",o,[["path",{d:"M7 2h10"}],["path",{d:"M5 6h14"}],["rect",{width:"18",height:"12",x:"3",y:"10",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q5=["svg",o,[["path",{d:"M3 2h18"}],["rect",{width:"18",height:"12",x:"3",y:"6",rx:"2"}],["path",{d:"M3 22h18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tg=["svg",o,[["line",{x1:"6",x2:"10",y1:"11",y2:"11"}],["line",{x1:"8",x2:"8",y1:"9",y2:"13"}],["line",{x1:"15",x2:"15.01",y1:"12",y2:"12"}],["line",{x1:"18",x2:"18.01",y1:"10",y2:"10"}],["path",{d:"M17.32 5H6.68a4 4 0 0 0-3.978 3.59c-.006.052-.01.101-.017.152C2.604 9.416 2 14.456 2 16a3 3 0 0 0 3 3c1 0 1.5-.5 2-1l1.414-1.414A2 2 0 0 1 9.828 16h4.344a2 2 0 0 1 1.414.586L17 18c.5.5 1 1 2 1a3 3 0 0 0 3-3c0-1.545-.604-6.584-.685-7.258-.007-.05-.011-.1-.017-.151A4 4 0 0 0 17.32 5z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const eg=["svg",o,[["line",{x1:"6",x2:"10",y1:"12",y2:"12"}],["line",{x1:"8",x2:"8",y1:"10",y2:"14"}],["line",{x1:"15",x2:"15.01",y1:"13",y2:"13"}],["line",{x1:"18",x2:"18.01",y1:"11",y2:"11"}],["rect",{width:"20",height:"12",x:"2",y:"6",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ws=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 8h7"}],["path",{d:"M8 12h6"}],["path",{d:"M11 16h5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sg=["svg",o,[["path",{d:"M8 6h10"}],["path",{d:"M6 12h9"}],["path",{d:"M11 18h7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ag=["svg",o,[["path",{d:"M15.6 2.7a10 10 0 1 0 5.7 5.7"}],["circle",{cx:"12",cy:"12",r:"2"}],["path",{d:"M13.4 10.6 19 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ig=["svg",o,[["path",{d:"m12 14 4-4"}],["path",{d:"M3.34 19a10 10 0 1 1 17.32 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ng=["svg",o,[["path",{d:"m14 13-7.5 7.5c-.83.83-2.17.83-3 0 0 0 0 0 0 0a2.12 2.12 0 0 1 0-3L11 10"}],["path",{d:"m16 16 6-6"}],["path",{d:"m8 8 6-6"}],["path",{d:"m9 7 8 8"}],["path",{d:"m21 11-8-8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const og=["svg",o,[["path",{d:"M6 3h12l4 6-10 13L2 9Z"}],["path",{d:"M11 3 8 9l4 13 4-13-3-6"}],["path",{d:"M2 9h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rg=["svg",o,[["path",{d:"M9 10h.01"}],["path",{d:"M15 10h.01"}],["path",{d:"M12 2a8 8 0 0 0-8 8v12l3-3 2.5 2.5L12 19l2.5 2.5L17 19l3 3V10a8 8 0 0 0-8-8z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hg=["svg",o,[["rect",{x:"3",y:"8",width:"18",height:"4",rx:"1"}],["path",{d:"M12 8v13"}],["path",{d:"M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"}],["path",{d:"M7.5 8a2.5 2.5 0 0 1 0-5A4.8 8 0 0 1 12 8a4.8 8 0 0 1 4.5-5 2.5 2.5 0 0 1 0 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cg=["svg",o,[["path",{d:"M6 3v12"}],["path",{d:"M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"}],["path",{d:"M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"}],["path",{d:"M15 6a9 9 0 0 0-9 9"}],["path",{d:"M18 15v6"}],["path",{d:"M21 18h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lg=["svg",o,[["line",{x1:"6",x2:"6",y1:"3",y2:"15"}],["circle",{cx:"18",cy:"6",r:"3"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M18 9a9 9 0 0 1-9 9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ns=["svg",o,[["circle",{cx:"12",cy:"12",r:"3"}],["line",{x1:"3",x2:"9",y1:"12",y2:"12"}],["line",{x1:"15",x2:"21",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dg=["svg",o,[["path",{d:"M12 3v6"}],["circle",{cx:"12",cy:"12",r:"3"}],["path",{d:"M12 15v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pg=["svg",o,[["circle",{cx:"5",cy:"6",r:"3"}],["path",{d:"M12 6h5a2 2 0 0 1 2 2v7"}],["path",{d:"m15 9-3-3 3-3"}],["circle",{cx:"19",cy:"18",r:"3"}],["path",{d:"M12 18H7a2 2 0 0 1-2-2V9"}],["path",{d:"m9 15 3 3-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gg=["svg",o,[["circle",{cx:"18",cy:"18",r:"3"}],["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M13 6h3a2 2 0 0 1 2 2v7"}],["path",{d:"M11 18H8a2 2 0 0 1-2-2V9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ug=["svg",o,[["circle",{cx:"12",cy:"18",r:"3"}],["circle",{cx:"6",cy:"6",r:"3"}],["circle",{cx:"18",cy:"6",r:"3"}],["path",{d:"M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9"}],["path",{d:"M12 12v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fg=["svg",o,[["circle",{cx:"5",cy:"6",r:"3"}],["path",{d:"M5 9v6"}],["circle",{cx:"5",cy:"18",r:"3"}],["path",{d:"M12 3v18"}],["circle",{cx:"19",cy:"6",r:"3"}],["path",{d:"M16 15.7A9 9 0 0 0 19 9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vg=["svg",o,[["circle",{cx:"18",cy:"18",r:"3"}],["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M6 21V9a9 9 0 0 0 9 9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xg=["svg",o,[["circle",{cx:"5",cy:"6",r:"3"}],["path",{d:"M5 9v12"}],["circle",{cx:"19",cy:"18",r:"3"}],["path",{d:"m15 9-3-3 3-3"}],["path",{d:"M12 6h5a2 2 0 0 1 2 2v7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mg=["svg",o,[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M6 9v12"}],["path",{d:"m21 3-6 6"}],["path",{d:"m21 9-6-6"}],["path",{d:"M18 11.5V15"}],["circle",{cx:"18",cy:"18",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mg=["svg",o,[["circle",{cx:"5",cy:"6",r:"3"}],["path",{d:"M5 9v12"}],["path",{d:"m15 9-3-3 3-3"}],["path",{d:"M12 6h5a2 2 0 0 1 2 2v3"}],["path",{d:"M19 15v6"}],["path",{d:"M22 18h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yg=["svg",o,[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M6 9v12"}],["path",{d:"M13 6h3a2 2 0 0 1 2 2v3"}],["path",{d:"M18 15v6"}],["path",{d:"M21 18h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bg=["svg",o,[["circle",{cx:"18",cy:"18",r:"3"}],["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M18 6V5"}],["path",{d:"M18 11v-1"}],["line",{x1:"6",x2:"6",y1:"9",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wg=["svg",o,[["circle",{cx:"18",cy:"18",r:"3"}],["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M13 6h3a2 2 0 0 1 2 2v7"}],["line",{x1:"6",x2:"6",y1:"9",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _g=["svg",o,[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kg=["svg",o,[["path",{d:"m22 13.29-3.33-10a.42.42 0 0 0-.14-.18.38.38 0 0 0-.22-.11.39.39 0 0 0-.23.07.42.42 0 0 0-.14.18l-2.26 6.67H8.32L6.1 3.26a.42.42 0 0 0-.1-.18.38.38 0 0 0-.26-.08.39.39 0 0 0-.23.07.42.42 0 0 0-.14.18L2 13.29a.74.74 0 0 0 .27.83L12 21l9.69-6.88a.71.71 0 0 0 .31-.83Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cg=["svg",o,[["path",{d:"M15.2 22H8.8a2 2 0 0 1-2-1.79L5 3h14l-1.81 17.21A2 2 0 0 1 15.2 22Z"}],["path",{d:"M6 12a5 5 0 0 1 6 0 5 5 0 0 0 6 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sg=["svg",o,[["circle",{cx:"6",cy:"15",r:"4"}],["circle",{cx:"18",cy:"15",r:"4"}],["path",{d:"M14 15a2 2 0 0 0-2-2 2 2 0 0 0-2 2"}],["path",{d:"M2.5 13 5 7c.7-1.3 1.4-2 3-2"}],["path",{d:"M21.5 13 19 7c-.7-1.3-1.5-2-3-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lg=["svg",o,[["path",{d:"M21.54 15H17a2 2 0 0 0-2 2v4.54"}],["path",{d:"M7 3.34V5a3 3 0 0 0 3 3v0a2 2 0 0 1 2 2v0c0 1.1.9 2 2 2v0a2 2 0 0 0 2-2v0c0-1.1.9-2 2-2h3.17"}],["path",{d:"M11 21.95V18a2 2 0 0 0-2-2v0a2 2 0 0 1-2-2v-1a2 2 0 0 0-2-2H2.05"}],["circle",{cx:"12",cy:"12",r:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ag=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"}],["path",{d:"M2 12h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hg=["svg",o,[["path",{d:"M12 13V2l8 4-8 4"}],["path",{d:"M20.55 10.23A9 9 0 1 1 8 4.94"}],["path",{d:"M8 10a5 5 0 1 0 8.9 2.02"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vg=["svg",o,[["path",{d:"M18 11.5V9a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v1.4"}],["path",{d:"M14 10V8a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"}],["path",{d:"M10 9.9V9a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v5"}],["path",{d:"M6 14v0a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"}],["path",{d:"M18 11v0a2 2 0 1 1 4 0v3a8 8 0 0 1-8 8h-4a8 8 0 0 1-8-8 2 2 0 1 1 4 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pg=["svg",o,[["path",{d:"M22 10v6M2 10l10-5 10 5-10 5z"}],["path",{d:"M6 12v5c3 3 9 3 12 0v-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dg=["svg",o,[["path",{d:"M22 5V2l-5.89 5.89"}],["circle",{cx:"16.6",cy:"15.89",r:"3"}],["circle",{cx:"8.11",cy:"7.4",r:"3"}],["circle",{cx:"12.35",cy:"11.65",r:"3"}],["circle",{cx:"13.91",cy:"5.85",r:"3"}],["circle",{cx:"18.15",cy:"10.09",r:"3"}],["circle",{cx:"6.56",cy:"13.2",r:"3"}],["circle",{cx:"10.8",cy:"17.44",r:"3"}],["circle",{cx:"5",cy:"19",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const js=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M3 12h18"}],["path",{d:"M12 3v18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H1=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M3 9h18"}],["path",{d:"M3 15h18"}],["path",{d:"M9 3v18"}],["path",{d:"M15 3v18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fg=["svg",o,[["circle",{cx:"12",cy:"9",r:"1"}],["circle",{cx:"19",cy:"9",r:"1"}],["circle",{cx:"5",cy:"9",r:"1"}],["circle",{cx:"12",cy:"15",r:"1"}],["circle",{cx:"19",cy:"15",r:"1"}],["circle",{cx:"5",cy:"15",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tg=["svg",o,[["circle",{cx:"9",cy:"12",r:"1"}],["circle",{cx:"9",cy:"5",r:"1"}],["circle",{cx:"9",cy:"19",r:"1"}],["circle",{cx:"15",cy:"12",r:"1"}],["circle",{cx:"15",cy:"5",r:"1"}],["circle",{cx:"15",cy:"19",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bg=["svg",o,[["circle",{cx:"12",cy:"5",r:"1"}],["circle",{cx:"19",cy:"5",r:"1"}],["circle",{cx:"5",cy:"5",r:"1"}],["circle",{cx:"12",cy:"12",r:"1"}],["circle",{cx:"19",cy:"12",r:"1"}],["circle",{cx:"5",cy:"12",r:"1"}],["circle",{cx:"12",cy:"19",r:"1"}],["circle",{cx:"19",cy:"19",r:"1"}],["circle",{cx:"5",cy:"19",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Og=["svg",o,[["path",{d:"M3 7V5c0-1.1.9-2 2-2h2"}],["path",{d:"M17 3h2c1.1 0 2 .9 2 2v2"}],["path",{d:"M21 17v2c0 1.1-.9 2-2 2h-2"}],["path",{d:"M7 21H5c-1.1 0-2-.9-2-2v-2"}],["rect",{width:"7",height:"5",x:"7",y:"7",rx:"1"}],["rect",{width:"7",height:"5",x:"10",y:"12",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Eg=["svg",o,[["path",{d:"m20 7 1.7-1.7a1 1 0 0 0 0-1.4l-1.6-1.6a1 1 0 0 0-1.4 0L17 4v3Z"}],["path",{d:"m17 7-5.1 5.1"}],["circle",{cx:"11.5",cy:"12.5",r:".5"}],["path",{d:"M6 12a2 2 0 0 0 1.8-1.2l.4-.9C8.7 8.8 9.8 8 11 8c2.8 0 5 2.2 5 5 0 1.2-.8 2.3-1.9 2.8l-.9.4A2 2 0 0 0 12 18a4 4 0 0 1-4 4c-3.3 0-6-2.7-6-6a4 4 0 0 1 4-4"}],["path",{d:"m6 16 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rg=["svg",o,[["path",{d:"m15 12-8.5 8.5c-.83.83-2.17.83-3 0 0 0 0 0 0 0a2.12 2.12 0 0 1 0-3L12 9"}],["path",{d:"M17.64 15 22 10.64"}],["path",{d:"m20.91 11.7-1.25-1.25c-.6-.6-.93-1.4-.93-2.25v-.86L16.01 4.6a5.56 5.56 0 0 0-3.94-1.64H9l.92.82A6.18 6.18 0 0 1 12 8.4v1.56l2 2h2.47l2.26 1.91"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zg=["svg",o,[["path",{d:"M18 12.5V10a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v1.4"}],["path",{d:"M14 11V9a2 2 0 1 0-4 0v2"}],["path",{d:"M10 10.5V5a2 2 0 1 0-4 0v9"}],["path",{d:"m7 15-1.76-1.76a2 2 0 0 0-2.83 2.82l3.6 3.6C7.5 21.14 9.2 22 12 22h2a8 8 0 0 0 8-8V7a2 2 0 1 0-4 0v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ig=["svg",o,[["path",{d:"M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"}],["path",{d:"M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"}],["path",{d:"M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"}],["path",{d:"M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $g=["svg",o,[["path",{d:"M12 2v8"}],["path",{d:"m16 6-4 4-4-4"}],["rect",{width:"20",height:"8",x:"2",y:"14",rx:"2"}],["path",{d:"M6 18h.01"}],["path",{d:"M10 18h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zg=["svg",o,[["path",{d:"m16 6-4-4-4 4"}],["path",{d:"M12 2v8"}],["rect",{width:"20",height:"8",x:"2",y:"14",rx:"2"}],["path",{d:"M6 18h.01"}],["path",{d:"M10 18h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wg=["svg",o,[["line",{x1:"22",x2:"2",y1:"12",y2:"12"}],["path",{d:"M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"}],["line",{x1:"6",x2:"6.01",y1:"16",y2:"16"}],["line",{x1:"10",x2:"10.01",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ng=["svg",o,[["path",{d:"M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v2z"}],["path",{d:"M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5"}],["path",{d:"M4 15v-3a6 6 0 0 1 6-6h0"}],["path",{d:"M14 6h0a6 6 0 0 1 6 6v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jg=["svg",o,[["line",{x1:"4",x2:"20",y1:"9",y2:"9"}],["line",{x1:"4",x2:"20",y1:"15",y2:"15"}],["line",{x1:"10",x2:"8",y1:"3",y2:"21"}],["line",{x1:"16",x2:"14",y1:"3",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ug=["svg",o,[["path",{d:"m5.2 6.2 1.4 1.4"}],["path",{d:"M2 13h2"}],["path",{d:"M20 13h2"}],["path",{d:"m17.4 7.6 1.4-1.4"}],["path",{d:"M22 17H2"}],["path",{d:"M22 21H2"}],["path",{d:"M16 13a4 4 0 0 0-8 0"}],["path",{d:"M12 5V2.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qg=["svg",o,[["path",{d:"M22 9a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h1l2 2h12l2-2h1a1 1 0 0 0 1-1Z"}],["path",{d:"M7.5 12h9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gg=["svg",o,[["path",{d:"M4 12h8"}],["path",{d:"M4 18V6"}],["path",{d:"M12 18V6"}],["path",{d:"m17 12 3-2v8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xg=["svg",o,[["path",{d:"M4 12h8"}],["path",{d:"M4 18V6"}],["path",{d:"M12 18V6"}],["path",{d:"M21 18h-4c0-4 4-3 4-6 0-1.5-2-2.5-4-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yg=["svg",o,[["path",{d:"M4 12h8"}],["path",{d:"M4 18V6"}],["path",{d:"M12 18V6"}],["path",{d:"M17.5 10.5c1.7-1 3.5 0 3.5 1.5a2 2 0 0 1-2 2"}],["path",{d:"M17 17.5c2 1.5 4 .3 4-1.5a2 2 0 0 0-2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kg=["svg",o,[["path",{d:"M4 12h8"}],["path",{d:"M4 18V6"}],["path",{d:"M12 18V6"}],["path",{d:"M17 10v4h4"}],["path",{d:"M21 10v8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jg=["svg",o,[["path",{d:"M4 12h8"}],["path",{d:"M4 18V6"}],["path",{d:"M12 18V6"}],["path",{d:"M17 13v-3h4"}],["path",{d:"M17 17.7c.4.2.8.3 1.3.3 1.5 0 2.7-1.1 2.7-2.5S19.8 13 18.3 13H17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qg=["svg",o,[["path",{d:"M4 12h8"}],["path",{d:"M4 18V6"}],["path",{d:"M12 18V6"}],["circle",{cx:"19",cy:"16",r:"2"}],["path",{d:"M20 10c-2 2-3 3.5-3 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tu=["svg",o,[["path",{d:"M6 12h12"}],["path",{d:"M6 20V4"}],["path",{d:"M18 20V4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const eu=["svg",o,[["path",{d:"M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const su=["svg",o,[["path",{d:"M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"}],["path",{d:"m12 13-1-1 2-2-3-3 2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const au=["svg",o,[["path",{d:"M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"}],["path",{d:"M12 5 9.04 7.96a2.17 2.17 0 0 0 0 3.08v0c.82.82 2.13.85 3 .07l2.07-1.9a2.82 2.82 0 0 1 3.79 0l2.96 2.66"}],["path",{d:"m18 15-2-2"}],["path",{d:"m15 18-2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const iu=["svg",o,[["line",{x1:"2",y1:"2",x2:"22",y2:"22"}],["path",{d:"M16.5 16.5 12 21l-7-7c-1.5-1.45-3-3.2-3-5.5a5.5 5.5 0 0 1 2.14-4.35"}],["path",{d:"M8.76 3.1c1.15.22 2.13.78 3.24 1.9 1.5-1.5 2.74-2 4.5-2A5.5 5.5 0 0 1 22 8.5c0 2.12-1.3 3.78-2.67 5.17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nu=["svg",o,[["path",{d:"M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"}],["path",{d:"M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ou=["svg",o,[["path",{d:"M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ru=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hu=["svg",o,[["path",{d:"m3 15 5.12-5.12A3 3 0 0 1 10.24 9H13a2 2 0 1 1 0 4h-2.5m4-.68 4.17-4.89a1.88 1.88 0 0 1 2.92 2.36l-4.2 5.94A3 3 0 0 1 14.96 17H9.83a2 2 0 0 0-1.42.59L7 19"}],["path",{d:"m2 14 6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cu=["svg",o,[["path",{d:"M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lu=["svg",o,[["path",{d:"m9 11-6 6v3h9l3-3"}],["path",{d:"m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const du=["svg",o,[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"}],["path",{d:"M3 3v5h5"}],["path",{d:"M12 7v5l4 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pu=["svg",o,[["path",{d:"m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"}],["polyline",{points:"9 22 9 12 15 12 15 22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gu=["svg",o,[["path",{d:"M17.5 5.5C19 7 20.5 9 21 11c-1.323.265-2.646.39-4.118.226"}],["path",{d:"M5.5 17.5C7 19 9 20.5 11 21c.5-2.5.5-5-1-8.5"}],["path",{d:"M17.5 17.5c-2.5 0-4 0-6-1"}],["path",{d:"M20 11.5c1 1.5 2 3.5 2 4.5"}],["path",{d:"M11.5 20c1.5 1 3.5 2 4.5 2 .5-1.5 0-3-.5-4.5"}],["path",{d:"M22 22c-2 0-3.5-.5-5.5-1.5"}],["path",{d:"M4.783 4.782C1.073 8.492 1 14.5 5 18c1-1 2-4.5 1.5-6.5 1.5 1 4 1 5.5.5M8.227 2.57C11.578 1.335 15.453 2.089 18 5c-.88.88-3.7 1.761-5.726 1.618"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uu=["svg",o,[["path",{d:"M17.5 5.5C19 7 20.5 9 21 11c-2.5.5-5 .5-8.5-1"}],["path",{d:"M5.5 17.5C7 19 9 20.5 11 21c.5-2.5.5-5-1-8.5"}],["path",{d:"M16.5 11.5c1 2 1 3.5 1 6-2.5 0-4 0-6-1"}],["path",{d:"M20 11.5c1 1.5 2 3.5 2 4.5-1.5.5-3 0-4.5-.5"}],["path",{d:"M11.5 20c1.5 1 3.5 2 4.5 2 .5-1.5 0-3-.5-4.5"}],["path",{d:"M20.5 16.5c1 2 1.5 3.5 1.5 5.5-2 0-3.5-.5-5.5-1.5"}],["path",{d:"M4.783 4.782C8.493 1.072 14.5 1 18 5c-1 1-4.5 2-6.5 1.5 1 1.5 1 4 .5 5.5-1.5.5-4 .5-5.5-.5C7 13.5 6 17 5 18c-4-3.5-3.927-9.508-.217-13.218Z"}],["path",{d:"M4.5 4.5 3 3c-.184-.185-.184-.816 0-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fu=["svg",o,[["path",{d:"M18 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2Z"}],["path",{d:"m9 16 .348-.24c1.465-1.013 3.84-1.013 5.304 0L15 16"}],["path",{d:"M8 7h.01"}],["path",{d:"M16 7h.01"}],["path",{d:"M12 7h.01"}],["path",{d:"M12 11h.01"}],["path",{d:"M16 11h.01"}],["path",{d:"M8 11h.01"}],["path",{d:"M10 22v-6.5m4 0V22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vu=["svg",o,[["path",{d:"M5 22h14"}],["path",{d:"M5 2h14"}],["path",{d:"M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"}],["path",{d:"M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xu=["svg",o,[["path",{d:"M12 17c5 0 8-2.69 8-6H4c0 3.31 3 6 8 6Zm-4 4h8m-4-3v3M5.14 11a3.5 3.5 0 1 1 6.71 0"}],["path",{d:"M12.14 11a3.5 3.5 0 1 1 6.71 0"}],["path",{d:"M15.5 6.5a3.5 3.5 0 1 0-7 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mu=["svg",o,[["path",{d:"m7 11 4.08 10.35a1 1 0 0 0 1.84 0L17 11"}],["path",{d:"M17 7A5 5 0 0 0 7 7"}],["path",{d:"M17 7a2 2 0 0 1 0 4H7a2 2 0 0 1 0-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mu=["svg",o,[["circle",{cx:"9",cy:"9",r:"2"}],["path",{d:"M10.3 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10.8"}],["path",{d:"m21 15-3.1-3.1a2 2 0 0 0-2.814.014L6 21"}],["path",{d:"m14 19.5 3 3v-6"}],["path",{d:"m17 22.5 3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yu=["svg",o,[["path",{d:"M21 9v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7"}],["line",{x1:"16",x2:"22",y1:"5",y2:"5"}],["circle",{cx:"9",cy:"9",r:"2"}],["path",{d:"m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bu=["svg",o,[["line",{x1:"2",x2:"22",y1:"2",y2:"22"}],["path",{d:"M10.41 10.41a2 2 0 1 1-2.83-2.83"}],["line",{x1:"13.5",x2:"6",y1:"13.5",y2:"21"}],["line",{x1:"18",x2:"21",y1:"12",y2:"15"}],["path",{d:"M3.59 3.59A1.99 1.99 0 0 0 3 5v14a2 2 0 0 0 2 2h14c.55 0 1.052-.22 1.41-.59"}],["path",{d:"M21 15V5a2 2 0 0 0-2-2H9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wu=["svg",o,[["path",{d:"M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7"}],["line",{x1:"16",x2:"22",y1:"5",y2:"5"}],["line",{x1:"19",x2:"19",y1:"2",y2:"8"}],["circle",{cx:"9",cy:"9",r:"2"}],["path",{d:"m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _u=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["circle",{cx:"9",cy:"9",r:"2"}],["path",{d:"m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ku=["svg",o,[["path",{d:"M12 3v12"}],["path",{d:"m8 11 4 4 4-4"}],["path",{d:"M8 5H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cu=["svg",o,[["polyline",{points:"22 12 16 12 14 15 10 15 8 12 2 12"}],["path",{d:"M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Su=["svg",o,[["polyline",{points:"3 8 7 12 3 16"}],["line",{x1:"21",x2:"11",y1:"12",y2:"12"}],["line",{x1:"21",x2:"11",y1:"6",y2:"6"}],["line",{x1:"21",x2:"11",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lu=["svg",o,[["path",{d:"M6 3h12"}],["path",{d:"M6 8h12"}],["path",{d:"m6 13 8.5 8"}],["path",{d:"M6 13h3"}],["path",{d:"M9 13c6.667 0 6.667-10 0-10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Au=["svg",o,[["path",{d:"M12 12c-2-2.67-4-4-6-4a4 4 0 1 0 0 8c2 0 4-1.33 6-4Zm0 0c2 2.67 4 4 6 4a4 4 0 0 0 0-8c-2 0-4 1.33-6 4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hu=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 16v-4"}],["path",{d:"M12 8h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vu=["svg",o,[["rect",{width:"20",height:"20",x:"2",y:"2",rx:"5",ry:"5"}],["path",{d:"M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"}],["line",{x1:"17.5",x2:"17.51",y1:"6.5",y2:"6.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pu=["svg",o,[["line",{x1:"19",x2:"10",y1:"4",y2:"4"}],["line",{x1:"14",x2:"5",y1:"20",y2:"20"}],["line",{x1:"15",x2:"9",y1:"4",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Du=["svg",o,[["path",{d:"M20 10c0-4.4-3.6-8-8-8s-8 3.6-8 8 3.6 8 8 8h8"}],["polyline",{points:"16 14 20 18 16 22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fu=["svg",o,[["path",{d:"M4 10c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8H4"}],["polyline",{points:"8 22 4 18 8 14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tu=["svg",o,[["path",{d:"M12 9.5V21m0-11.5L6 3m6 6.5L18 3"}],["path",{d:"M6 15h12"}],["path",{d:"M6 11h12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bu=["svg",o,[["path",{d:"M21 17a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2Z"}],["path",{d:"M6 15v-2"}],["path",{d:"M12 15V9"}],["circle",{cx:"12",cy:"6",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Us=["svg",o,[["path",{d:"M8 7v7"}],["path",{d:"M12 7v4"}],["path",{d:"M16 7v9"}],["path",{d:"M5 3a2 2 0 0 0-2 2"}],["path",{d:"M9 3h1"}],["path",{d:"M14 3h1"}],["path",{d:"M19 3a2 2 0 0 1 2 2"}],["path",{d:"M21 9v1"}],["path",{d:"M21 14v1"}],["path",{d:"M21 19a2 2 0 0 1-2 2"}],["path",{d:"M14 21h1"}],["path",{d:"M9 21h1"}],["path",{d:"M5 21a2 2 0 0 1-2-2"}],["path",{d:"M3 14v1"}],["path",{d:"M3 9v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qs=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M8 7v7"}],["path",{d:"M12 7v4"}],["path",{d:"M16 7v9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ou=["svg",o,[["path",{d:"M6 5v11"}],["path",{d:"M12 5v6"}],["path",{d:"M18 5v14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Eu=["svg",o,[["path",{d:"M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z"}],["circle",{cx:"16.5",cy:"7.5",r:".5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ru=["svg",o,[["path",{d:"M12.4 2.7c.9-.9 2.5-.9 3.4 0l5.5 5.5c.9.9.9 2.5 0 3.4l-3.7 3.7c-.9.9-2.5.9-3.4 0L8.7 9.8c-.9-.9-.9-2.5 0-3.4Z"}],["path",{d:"m14 7 3 3"}],["path",{d:"M9.4 10.6 2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zu=["svg",o,[["circle",{cx:"7.5",cy:"15.5",r:"5.5"}],["path",{d:"m21 2-9.6 9.6"}],["path",{d:"m15.5 7.5 3 3L22 7l-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Iu=["svg",o,[["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}],["path",{d:"M6 8h4"}],["path",{d:"M14 8h.01"}],["path",{d:"M18 8h.01"}],["path",{d:"M2 12h20"}],["path",{d:"M6 12v4"}],["path",{d:"M10 12v4"}],["path",{d:"M14 12v4"}],["path",{d:"M18 12v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $u=["svg",o,[["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2",ry:"2"}],["path",{d:"M6 8h.001"}],["path",{d:"M10 8h.001"}],["path",{d:"M14 8h.001"}],["path",{d:"M18 8h.001"}],["path",{d:"M8 12h.001"}],["path",{d:"M12 12h.001"}],["path",{d:"M16 12h.001"}],["path",{d:"M7 16h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zu=["svg",o,[["path",{d:"M12 2v5"}],["path",{d:"M6 7h12l4 9H2l4-9Z"}],["path",{d:"M9.17 16a3 3 0 1 0 5.66 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wu=["svg",o,[["path",{d:"m14 5-3 3 2 7 8-8-7-2Z"}],["path",{d:"m14 5-3 3-3-3 3-3 3 3Z"}],["path",{d:"M9.5 6.5 4 12l3 6"}],["path",{d:"M3 22v-2c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v2H3Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nu=["svg",o,[["path",{d:"M9 2h6l3 7H6l3-7Z"}],["path",{d:"M12 9v13"}],["path",{d:"M9 22h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ju=["svg",o,[["path",{d:"M11 13h6l3 7H8l3-7Z"}],["path",{d:"M14 13V8a2 2 0 0 0-2-2H8"}],["path",{d:"M4 9h2a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H4v6Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uu=["svg",o,[["path",{d:"M11 4h6l3 7H8l3-7Z"}],["path",{d:"M14 11v5a2 2 0 0 1-2 2H8"}],["path",{d:"M4 15h2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H4v-6Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qu=["svg",o,[["path",{d:"M8 2h8l4 10H4L8 2Z"}],["path",{d:"M12 12v6"}],["path",{d:"M8 22v-2c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v2H8Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gu=["svg",o,[["path",{d:"m12 8 6-3-6-3v10"}],["path",{d:"m8 11.99-5.5 3.14a1 1 0 0 0 0 1.74l8.5 4.86a2 2 0 0 0 2 0l8.5-4.86a1 1 0 0 0 0-1.74L16 12"}],["path",{d:"m6.49 12.85 11.02 6.3"}],["path",{d:"M17.51 12.85 6.5 19.15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xu=["svg",o,[["line",{x1:"3",x2:"21",y1:"22",y2:"22"}],["line",{x1:"6",x2:"6",y1:"18",y2:"11"}],["line",{x1:"10",x2:"10",y1:"18",y2:"11"}],["line",{x1:"14",x2:"14",y1:"18",y2:"11"}],["line",{x1:"18",x2:"18",y1:"18",y2:"11"}],["polygon",{points:"12 2 20 7 4 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yu=["svg",o,[["path",{d:"m5 8 6 6"}],["path",{d:"m4 14 6-6 2-3"}],["path",{d:"M2 5h12"}],["path",{d:"M7 2h1"}],["path",{d:"m22 22-5-10-5 10"}],["path",{d:"M14 18h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ku=["svg",o,[["rect",{width:"18",height:"12",x:"3",y:"4",rx:"2",ry:"2"}],["line",{x1:"2",x2:"22",y1:"20",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ju=["svg",o,[["path",{d:"M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45L4 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qu=["svg",o,[["path",{d:"M7 22a5 5 0 0 1-2-4"}],["path",{d:"M7 16.93c.96.43 1.96.74 2.99.91"}],["path",{d:"M3.34 14A6.8 6.8 0 0 1 2 10c0-4.42 4.48-8 10-8s10 3.58 10 8a7.19 7.19 0 0 1-.33 2"}],["path",{d:"M5 18a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"}],["path",{d:"M14.33 22h-.09a.35.35 0 0 1-.24-.32v-10a.34.34 0 0 1 .33-.34c.08 0 .15.03.21.08l7.34 6a.33.33 0 0 1-.21.59h-4.49l-2.57 3.85a.35.35 0 0 1-.28.14v0z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t3=["svg",o,[["path",{d:"M7 22a5 5 0 0 1-2-4"}],["path",{d:"M3.3 14A6.8 6.8 0 0 1 2 10c0-4.4 4.5-8 10-8s10 3.6 10 8-4.5 8-10 8a12 12 0 0 1-5-1"}],["path",{d:"M5 18a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e3=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M18 13a6 6 0 0 1-6 5 6 6 0 0 1-6-5h12Z"}],["line",{x1:"9",x2:"9.01",y1:"9",y2:"9"}],["line",{x1:"15",x2:"15.01",y1:"9",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s3=["svg",o,[["path",{d:"m16.02 12 5.48 3.13a1 1 0 0 1 0 1.74L13 21.74a2 2 0 0 1-2 0l-8.5-4.87a1 1 0 0 1 0-1.74L7.98 12"}],["path",{d:"M13 13.74a2 2 0 0 1-2 0L2.5 8.87a1 1 0 0 1 0-1.74L11 2.26a2 2 0 0 1 2 0l8.5 4.87a1 1 0 0 1 0 1.74Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a3=["svg",o,[["path",{d:"m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"}],["path",{d:"m6.08 9.5-3.5 1.6a1 1 0 0 0 0 1.81l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9a1 1 0 0 0 0-1.83l-3.5-1.59"}],["path",{d:"m6.08 14.5-3.5 1.6a1 1 0 0 0 0 1.81l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9a1 1 0 0 0 0-1.83l-3.5-1.59"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i3=["svg",o,[["path",{d:"m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"}],["path",{d:"m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"}],["path",{d:"m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n3=["svg",o,[["rect",{width:"7",height:"9",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"5",x:"14",y:"3",rx:"1"}],["rect",{width:"7",height:"9",x:"14",y:"12",rx:"1"}],["rect",{width:"7",height:"5",x:"3",y:"16",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o3=["svg",o,[["rect",{width:"7",height:"7",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"7",x:"14",y:"3",rx:"1"}],["rect",{width:"7",height:"7",x:"14",y:"14",rx:"1"}],["rect",{width:"7",height:"7",x:"3",y:"14",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r3=["svg",o,[["rect",{width:"7",height:"7",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"7",x:"3",y:"14",rx:"1"}],["path",{d:"M14 4h7"}],["path",{d:"M14 9h7"}],["path",{d:"M14 15h7"}],["path",{d:"M14 20h7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h3=["svg",o,[["rect",{width:"7",height:"18",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"7",x:"14",y:"3",rx:"1"}],["rect",{width:"7",height:"7",x:"14",y:"14",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c3=["svg",o,[["rect",{width:"18",height:"7",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"7",x:"3",y:"14",rx:"1"}],["rect",{width:"7",height:"7",x:"14",y:"14",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l3=["svg",o,[["rect",{width:"18",height:"7",x:"3",y:"3",rx:"1"}],["rect",{width:"9",height:"7",x:"3",y:"14",rx:"1"}],["rect",{width:"5",height:"7",x:"16",y:"14",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d3=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"9",y2:"9"}],["line",{x1:"9",x2:"9",y1:"21",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p3=["svg",o,[["path",{d:"M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"}],["path",{d:"M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g3=["svg",o,[["path",{d:"M2 22c1.25-.987 2.27-1.975 3.9-2.2a5.56 5.56 0 0 1 3.8 1.5 4 4 0 0 0 6.187-2.353 3.5 3.5 0 0 0 3.69-5.116A3.5 3.5 0 0 0 20.95 8 3.5 3.5 0 1 0 16 3.05a3.5 3.5 0 0 0-5.831 1.373 3.5 3.5 0 0 0-5.116 3.69 4 4 0 0 0-2.348 6.155C3.499 15.42 4.409 16.712 4.2 18.1 3.926 19.743 3.014 20.732 2 22"}],["path",{d:"M2 22 17 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u3=["svg",o,[["rect",{width:"8",height:"18",x:"3",y:"3",rx:"1"}],["path",{d:"M7 3v18"}],["path",{d:"M20.4 18.9c.2.5-.1 1.1-.6 1.3l-1.9.7c-.5.2-1.1-.1-1.3-.6L11.1 5.1c-.2-.5.1-1.1.6-1.3l1.9-.7c.5-.2 1.1.1 1.3.6Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f3=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M7 7v10"}],["path",{d:"M11 7v10"}],["path",{d:"m15 7 2 10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v3=["svg",o,[["path",{d:"m16 6 4 14"}],["path",{d:"M12 6v14"}],["path",{d:"M8 8v12"}],["path",{d:"M4 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x3=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m4.93 4.93 4.24 4.24"}],["path",{d:"m14.83 9.17 4.24-4.24"}],["path",{d:"m14.83 14.83 4.24 4.24"}],["path",{d:"m9.17 14.83-4.24 4.24"}],["circle",{cx:"12",cy:"12",r:"4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m3=["svg",o,[["path",{d:"M8 20V8c0-2.2 1.8-4 4-4 1.5 0 2.8.8 3.5 2"}],["path",{d:"M6 12h4"}],["path",{d:"M14 12h2v8"}],["path",{d:"M6 20h4"}],["path",{d:"M14 20h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M3=["svg",o,[["path",{d:"M16.8 11.2c.8-.9 1.2-2 1.2-3.2a6 6 0 0 0-9.3-5"}],["path",{d:"m2 2 20 20"}],["path",{d:"M6.3 6.3a4.67 4.67 0 0 0 1.2 5.2c.7.7 1.3 1.5 1.5 2.5"}],["path",{d:"M9 18h6"}],["path",{d:"M10 22h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y3=["svg",o,[["path",{d:"M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"}],["path",{d:"M9 18h6"}],["path",{d:"M10 22h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b3=["svg",o,[["path",{d:"M3 3v18h18"}],["path",{d:"m19 9-5 5-4-4-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w3=["svg",o,[["path",{d:"M9 17H7A5 5 0 0 1 7 7"}],["path",{d:"M15 7h2a5 5 0 0 1 4 8"}],["line",{x1:"8",x2:"12",y1:"12",y2:"12"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _3=["svg",o,[["path",{d:"M9 17H7A5 5 0 0 1 7 7h2"}],["path",{d:"M15 7h2a5 5 0 1 1 0 10h-2"}],["line",{x1:"8",x2:"16",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k3=["svg",o,[["path",{d:"M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"}],["path",{d:"M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C3=["svg",o,[["path",{d:"M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"}],["rect",{width:"4",height:"12",x:"2",y:"9"}],["circle",{cx:"4",cy:"4",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S3=["svg",o,[["path",{d:"m3 17 2 2 4-4"}],["path",{d:"m3 7 2 2 4-4"}],["path",{d:"M13 6h8"}],["path",{d:"M13 12h8"}],["path",{d:"M13 18h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L3=["svg",o,[["path",{d:"M16 12H3"}],["path",{d:"M16 6H3"}],["path",{d:"M10 18H3"}],["path",{d:"M21 6v10a2 2 0 0 1-2 2h-5"}],["path",{d:"m16 16-2 2 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A3=["svg",o,[["path",{d:"M3 6h18"}],["path",{d:"M7 12h10"}],["path",{d:"M10 18h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H3=["svg",o,[["path",{d:"M11 12H3"}],["path",{d:"M16 6H3"}],["path",{d:"M16 18H3"}],["path",{d:"M21 12h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V3=["svg",o,[["path",{d:"M21 15V6"}],["path",{d:"M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"}],["path",{d:"M12 12H3"}],["path",{d:"M16 6H3"}],["path",{d:"M12 18H3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P3=["svg",o,[["line",{x1:"10",x2:"21",y1:"6",y2:"6"}],["line",{x1:"10",x2:"21",y1:"12",y2:"12"}],["line",{x1:"10",x2:"21",y1:"18",y2:"18"}],["path",{d:"M4 6h1v4"}],["path",{d:"M4 10h2"}],["path",{d:"M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D3=["svg",o,[["path",{d:"M11 12H3"}],["path",{d:"M16 6H3"}],["path",{d:"M16 18H3"}],["path",{d:"M18 9v6"}],["path",{d:"M21 12h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F3=["svg",o,[["path",{d:"M21 6H3"}],["path",{d:"M7 12H3"}],["path",{d:"M7 18H3"}],["path",{d:"M12 18a5 5 0 0 0 9-3 4.5 4.5 0 0 0-4.5-4.5c-1.33 0-2.54.54-3.41 1.41L11 14"}],["path",{d:"M11 10v4h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T3=["svg",o,[["path",{d:"M16 12H3"}],["path",{d:"M16 18H3"}],["path",{d:"M10 6H3"}],["path",{d:"M21 18V8a2 2 0 0 0-2-2h-5"}],["path",{d:"m16 8-2-2 2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B3=["svg",o,[["rect",{x:"3",y:"5",width:"6",height:"6",rx:"1"}],["path",{d:"m3 17 2 2 4-4"}],["path",{d:"M13 6h8"}],["path",{d:"M13 12h8"}],["path",{d:"M13 18h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O3=["svg",o,[["path",{d:"M21 12h-8"}],["path",{d:"M21 6H8"}],["path",{d:"M21 18h-8"}],["path",{d:"M3 6v4c0 1.1.9 2 2 2h3"}],["path",{d:"M3 10v6c0 1.1.9 2 2 2h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E3=["svg",o,[["path",{d:"M12 12H3"}],["path",{d:"M16 6H3"}],["path",{d:"M12 18H3"}],["path",{d:"m16 12 5 3-5 3v-6Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R3=["svg",o,[["path",{d:"M11 12H3"}],["path",{d:"M16 6H3"}],["path",{d:"M16 18H3"}],["path",{d:"m19 10-4 4"}],["path",{d:"m15 10 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z3=["svg",o,[["line",{x1:"8",x2:"21",y1:"6",y2:"6"}],["line",{x1:"8",x2:"21",y1:"12",y2:"12"}],["line",{x1:"8",x2:"21",y1:"18",y2:"18"}],["line",{x1:"3",x2:"3.01",y1:"6",y2:"6"}],["line",{x1:"3",x2:"3.01",y1:"12",y2:"12"}],["line",{x1:"3",x2:"3.01",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I3=["svg",o,[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $3=["svg",o,[["line",{x1:"12",x2:"12",y1:"2",y2:"6"}],["line",{x1:"12",x2:"12",y1:"18",y2:"22"}],["line",{x1:"4.93",x2:"7.76",y1:"4.93",y2:"7.76"}],["line",{x1:"16.24",x2:"19.07",y1:"16.24",y2:"19.07"}],["line",{x1:"2",x2:"6",y1:"12",y2:"12"}],["line",{x1:"18",x2:"22",y1:"12",y2:"12"}],["line",{x1:"4.93",x2:"7.76",y1:"19.07",y2:"16.24"}],["line",{x1:"16.24",x2:"19.07",y1:"7.76",y2:"4.93"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z3=["svg",o,[["line",{x1:"2",x2:"5",y1:"12",y2:"12"}],["line",{x1:"19",x2:"22",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"2",y2:"5"}],["line",{x1:"12",x2:"12",y1:"19",y2:"22"}],["circle",{cx:"12",cy:"12",r:"7"}],["circle",{cx:"12",cy:"12",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W3=["svg",o,[["line",{x1:"2",x2:"5",y1:"12",y2:"12"}],["line",{x1:"19",x2:"22",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"2",y2:"5"}],["line",{x1:"12",x2:"12",y1:"19",y2:"22"}],["path",{d:"M7.11 7.11C5.83 8.39 5 10.1 5 12c0 3.87 3.13 7 7 7 1.9 0 3.61-.83 4.89-2.11"}],["path",{d:"M18.71 13.96c.19-.63.29-1.29.29-1.96 0-3.87-3.13-7-7-7-.67 0-1.33.1-1.96.29"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N3=["svg",o,[["line",{x1:"2",x2:"5",y1:"12",y2:"12"}],["line",{x1:"19",x2:"22",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"2",y2:"5"}],["line",{x1:"12",x2:"12",y1:"19",y2:"22"}],["circle",{cx:"12",cy:"12",r:"7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j3=["svg",o,[["circle",{cx:"12",cy:"16",r:"1"}],["rect",{x:"3",y:"10",width:"18",height:"12",rx:"2"}],["path",{d:"M7 10V7a5 5 0 0 1 10 0v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U3=["svg",o,[["rect",{width:"18",height:"11",x:"3",y:"11",rx:"2",ry:"2"}],["path",{d:"M7 11V7a5 5 0 0 1 10 0v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q3=["svg",o,[["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}],["polyline",{points:"10 17 15 12 10 7"}],["line",{x1:"15",x2:"3",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G3=["svg",o,[["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}],["polyline",{points:"16 17 21 12 16 7"}],["line",{x1:"21",x2:"9",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X3=["svg",o,[["circle",{cx:"11",cy:"11",r:"8"}],["path",{d:"m21 21-4.3-4.3"}],["path",{d:"M11 11a2 2 0 0 0 4 0 4 4 0 0 0-8 0 6 6 0 0 0 12 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y3=["svg",o,[["path",{d:"M6 20h0a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h0"}],["path",{d:"M8 18V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v14"}],["path",{d:"M10 20h4"}],["circle",{cx:"16",cy:"20",r:"2"}],["circle",{cx:"8",cy:"20",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K3=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M8 16V8l4 4 4-4v8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J3=["svg",o,[["path",{d:"m6 15-4-4 6.75-6.77a7.79 7.79 0 0 1 11 11L13 22l-4-4 6.39-6.36a2.14 2.14 0 0 0-3-3L6 15"}],["path",{d:"m5 8 4 4"}],["path",{d:"m12 15 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q3=["svg",o,[["path",{d:"M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}],["path",{d:"m16 19 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tf=["svg",o,[["path",{d:"M22 15V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}],["path",{d:"M16 19h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ef=["svg",o,[["path",{d:"M21.2 8.4c.5.38.8.97.8 1.6v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V10a2 2 0 0 1 .8-1.6l8-6a2 2 0 0 1 2.4 0l8 6Z"}],["path",{d:"m22 10-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sf=["svg",o,[["path",{d:"M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}],["path",{d:"M19 16v6"}],["path",{d:"M16 19h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const af=["svg",o,[["path",{d:"M22 10.5V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h12.5"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}],["path",{d:"M18 15.28c.2-.4.5-.8.9-1a2.1 2.1 0 0 1 2.6.4c.3.4.5.8.5 1.3 0 1.3-2 2-2 2"}],["path",{d:"M20 22v.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nf=["svg",o,[["path",{d:"M22 12.5V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h7.5"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}],["path",{d:"M18 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6v0Z"}],["circle",{cx:"18",cy:"18",r:"3"}],["path",{d:"m22 22-1.5-1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const of=["svg",o,[["path",{d:"M22 10.5V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h12.5"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}],["path",{d:"M20 14v4"}],["path",{d:"M20 22v.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rf=["svg",o,[["path",{d:"M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h9"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}],["path",{d:"m17 17 4 4"}],["path",{d:"m21 17-4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hf=["svg",o,[["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}],["path",{d:"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cf=["svg",o,[["path",{d:"M22 17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9.5C2 7 4 5 6.5 5H18c2.2 0 4 1.8 4 4v8Z"}],["polyline",{points:"15,9 18,9 18,11"}],["path",{d:"M6.5 5C9 5 11 7 11 9.5V17a2 2 0 0 1-2 2v0"}],["line",{x1:"6",x2:"7",y1:"10",y2:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lf=["svg",o,[["rect",{width:"16",height:"13",x:"6",y:"4",rx:"2"}],["path",{d:"m22 7-7.1 3.78c-.57.3-1.23.3-1.8 0L6 7"}],["path",{d:"M2 8v11c0 1.1.9 2 2 2h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const df=["svg",o,[["path",{d:"M5.43 5.43A8.06 8.06 0 0 0 4 10c0 6 8 12 8 12a29.94 29.94 0 0 0 5-5"}],["path",{d:"M19.18 13.52A8.66 8.66 0 0 0 20 10a8 8 0 0 0-8-8 7.88 7.88 0 0 0-3.52.82"}],["path",{d:"M9.13 9.13A2.78 2.78 0 0 0 9 10a3 3 0 0 0 3 3 2.78 2.78 0 0 0 .87-.13"}],["path",{d:"M14.9 9.25a3 3 0 0 0-2.15-2.16"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pf=["svg",o,[["path",{d:"M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"}],["circle",{cx:"12",cy:"10",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gf=["svg",o,[["path",{d:"M18 8c0 4.5-6 9-6 9s-6-4.5-6-9a6 6 0 0 1 12 0"}],["circle",{cx:"12",cy:"8",r:"2"}],["path",{d:"M8.835 14H5a1 1 0 0 0-.9.7l-2 6c-.1.1-.1.2-.1.3 0 .6.4 1 1 1h18c.6 0 1-.4 1-1 0-.1 0-.2-.1-.3l-2-6a1 1 0 0 0-.9-.7h-3.835"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uf=["svg",o,[["polygon",{points:"3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"}],["line",{x1:"9",x2:"9",y1:"3",y2:"18"}],["line",{x1:"15",x2:"15",y1:"6",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ff=["svg",o,[["path",{d:"M8 22h8"}],["path",{d:"M12 11v11"}],["path",{d:"m19 3-7 8-7-8Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vf=["svg",o,[["polyline",{points:"15 3 21 3 21 9"}],["polyline",{points:"9 21 3 21 3 15"}],["line",{x1:"21",x2:"14",y1:"3",y2:"10"}],["line",{x1:"3",x2:"10",y1:"21",y2:"14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xf=["svg",o,[["path",{d:"M8 3H5a2 2 0 0 0-2 2v3"}],["path",{d:"M21 8V5a2 2 0 0 0-2-2h-3"}],["path",{d:"M3 16v3a2 2 0 0 0 2 2h3"}],["path",{d:"M16 21h3a2 2 0 0 0 2-2v-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mf=["svg",o,[["path",{d:"M7.21 15 2.66 7.14a2 2 0 0 1 .13-2.2L4.4 2.8A2 2 0 0 1 6 2h12a2 2 0 0 1 1.6.8l1.6 2.14a2 2 0 0 1 .14 2.2L16.79 15"}],["path",{d:"M11 12 5.12 2.2"}],["path",{d:"m13 12 5.88-9.8"}],["path",{d:"M8 7h8"}],["circle",{cx:"12",cy:"17",r:"5"}],["path",{d:"M12 18v-2h-.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mf=["svg",o,[["path",{d:"M9.26 9.26 3 11v3l14.14 3.14"}],["path",{d:"M21 15.34V6l-7.31 2.03"}],["path",{d:"M11.6 16.8a3 3 0 1 1-5.8-1.6"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yf=["svg",o,[["path",{d:"m3 11 18-5v12L3 14v-3z"}],["path",{d:"M11.6 16.8a3 3 0 1 1-5.8-1.6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bf=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"8",x2:"16",y1:"15",y2:"15"}],["line",{x1:"9",x2:"9.01",y1:"9",y2:"9"}],["line",{x1:"15",x2:"15.01",y1:"9",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wf=["svg",o,[["path",{d:"M6 19v-3"}],["path",{d:"M10 19v-3"}],["path",{d:"M14 19v-3"}],["path",{d:"M18 19v-3"}],["path",{d:"M8 11V9"}],["path",{d:"M16 11V9"}],["path",{d:"M12 11V9"}],["path",{d:"M2 15h20"}],["path",{d:"M2 7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v1.1a2 2 0 0 0 0 3.837V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-5.1a2 2 0 0 0 0-3.837Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _f=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M7 8h10"}],["path",{d:"M7 12h10"}],["path",{d:"M7 16h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kf=["svg",o,[["line",{x1:"4",x2:"20",y1:"12",y2:"12"}],["line",{x1:"4",x2:"20",y1:"6",y2:"6"}],["line",{x1:"4",x2:"20",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cf=["svg",o,[["path",{d:"m8 6 4-4 4 4"}],["path",{d:"M12 2v10.3a4 4 0 0 1-1.172 2.872L4 22"}],["path",{d:"m20 22-5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sf=["svg",o,[["path",{d:"m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lf=["svg",o,[["path",{d:"M3 6V5c0-1.1.9-2 2-2h2"}],["path",{d:"M11 3h3"}],["path",{d:"M18 3h1c1.1 0 2 .9 2 2"}],["path",{d:"M21 9v2"}],["path",{d:"M21 15c0 1.1-.9 2-2 2h-1"}],["path",{d:"M14 17h-3"}],["path",{d:"m7 17-4 4v-5"}],["path",{d:"M3 12v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Af=["svg",o,[["path",{d:"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"}],["line",{x1:"9",x2:"15",y1:"10",y2:"10"}],["line",{x1:"12",x2:"12",y1:"7",y2:"13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hf=["svg",o,[["path",{d:"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vf=["svg",o,[["path",{d:"M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2v5Z"}],["path",{d:"M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pf=["svg",o,[["path",{d:"m12 8-9.04 9.06a2.82 2.82 0 1 0 3.98 3.98L16 12"}],["circle",{cx:"17",cy:"7",r:"5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Df=["svg",o,[["line",{x1:"2",x2:"22",y1:"2",y2:"22"}],["path",{d:"M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"}],["path",{d:"M5 10v2a7 7 0 0 0 12 5"}],["path",{d:"M15 9.34V5a3 3 0 0 0-5.68-1.33"}],["path",{d:"M9 9v3a3 3 0 0 0 5.12 2.12"}],["line",{x1:"12",x2:"12",y1:"19",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ff=["svg",o,[["path",{d:"M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"}],["path",{d:"M19 10v2a7 7 0 0 1-14 0v-2"}],["line",{x1:"12",x2:"12",y1:"19",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tf=["svg",o,[["path",{d:"M6 18h8"}],["path",{d:"M3 22h18"}],["path",{d:"M14 22a7 7 0 1 0 0-14h-1"}],["path",{d:"M9 14h2"}],["path",{d:"M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"}],["path",{d:"M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bf=["svg",o,[["rect",{width:"20",height:"15",x:"2",y:"4",rx:"2"}],["rect",{width:"8",height:"7",x:"6",y:"8",rx:"1"}],["path",{d:"M18 8v7"}],["path",{d:"M6 19v2"}],["path",{d:"M18 19v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Of=["svg",o,[["path",{d:"M18 6H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h13l4-3.5L18 6Z"}],["path",{d:"M12 13v8"}],["path",{d:"M12 3v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ef=["svg",o,[["path",{d:"M8 2h8"}],["path",{d:"M9 2v1.343M15 2v2.789a4 4 0 0 0 .672 2.219l.656.984a4 4 0 0 1 .672 2.22v1.131M7.8 7.8l-.128.192A4 4 0 0 0 7 10.212V20a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-3"}],["path",{d:"M7 15a6.47 6.47 0 0 1 5 0 6.472 6.472 0 0 0 3.435.435"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rf=["svg",o,[["path",{d:"M8 2h8"}],["path",{d:"M9 2v2.789a4 4 0 0 1-.672 2.219l-.656.984A4 4 0 0 0 7 10.212V20a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-9.789a4 4 0 0 0-.672-2.219l-.656-.984A4 4 0 0 1 15 4.788V2"}],["path",{d:"M7 15a6.472 6.472 0 0 1 5 0 6.47 6.47 0 0 0 5 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zf=["svg",o,[["polyline",{points:"4 14 10 14 10 20"}],["polyline",{points:"20 10 14 10 14 4"}],["line",{x1:"14",x2:"21",y1:"10",y2:"3"}],["line",{x1:"3",x2:"10",y1:"21",y2:"14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const If=["svg",o,[["path",{d:"M8 3v3a2 2 0 0 1-2 2H3"}],["path",{d:"M21 8h-3a2 2 0 0 1-2-2V3"}],["path",{d:"M3 16h3a2 2 0 0 1 2 2v3"}],["path",{d:"M16 21v-3a2 2 0 0 1 2-2h3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $f=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M8 12h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zf=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M8 12h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wf=["svg",o,[["path",{d:"M5 12h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nf=["svg",o,[["path",{d:"m9 10 2 2 4-4"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jf=["svg",o,[["circle",{cx:"19",cy:"6",r:"3"}],["path",{d:"M22 12v3a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uf=["svg",o,[["path",{d:"M12 13V7"}],["path",{d:"m15 10-3 3-3-3"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qf=["svg",o,[["path",{d:"M17 17H4a2 2 0 0 1-2-2V5c0-1.5 1-2 1-2"}],["path",{d:"M22 15V5a2 2 0 0 0-2-2H9"}],["path",{d:"M8 21h8"}],["path",{d:"M12 17v4"}],["path",{d:"m2 2 20 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gf=["svg",o,[["path",{d:"M10 13V7"}],["path",{d:"M14 13V7"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xf=["svg",o,[["path",{d:"m10 7 5 3-5 3Z"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yf=["svg",o,[["path",{d:"M18 8V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h8"}],["path",{d:"M10 19v-3.96 3.15"}],["path",{d:"M7 19h5"}],["rect",{width:"6",height:"10",x:"16",y:"12",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kf=["svg",o,[["path",{d:"M5.5 20H8"}],["path",{d:"M17 9h.01"}],["rect",{width:"10",height:"16",x:"12",y:"4",rx:"2"}],["path",{d:"M8 6H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h4"}],["circle",{cx:"17",cy:"15",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jf=["svg",o,[["rect",{x:"9",y:"7",width:"6",height:"6"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qf=["svg",o,[["path",{d:"m9 10 3-3 3 3"}],["path",{d:"M12 13V7"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t6=["svg",o,[["path",{d:"m14.5 12.5-5-5"}],["path",{d:"m9.5 12.5 5-5"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["path",{d:"M12 17v4"}],["path",{d:"M8 21h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e6=["svg",o,[["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}],["line",{x1:"8",x2:"16",y1:"21",y2:"21"}],["line",{x1:"12",x2:"12",y1:"17",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s6=["svg",o,[["path",{d:"M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"}],["path",{d:"M19 3v4"}],["path",{d:"M21 5h-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a6=["svg",o,[["path",{d:"M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i6=["svg",o,[["circle",{cx:"12",cy:"12",r:"1"}],["circle",{cx:"19",cy:"12",r:"1"}],["circle",{cx:"5",cy:"12",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n6=["svg",o,[["circle",{cx:"12",cy:"12",r:"1"}],["circle",{cx:"12",cy:"5",r:"1"}],["circle",{cx:"12",cy:"19",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o6=["svg",o,[["path",{d:"m8 3 4 8 5-5 5 15H2L8 3z"}],["path",{d:"M4.14 15.08c2.62-1.57 5.24-1.43 7.86.42 2.74 1.94 5.49 2 8.23.19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r6=["svg",o,[["path",{d:"m8 3 4 8 5-5 5 15H2L8 3z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h6=["svg",o,[["path",{d:"m4 4 7.07 17 2.51-7.39L21 11.07z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c6=["svg",o,[["path",{d:"m9 9 5 12 1.8-5.2L21 14Z"}],["path",{d:"M7.2 2.2 8 5.1"}],["path",{d:"m5.1 8-2.9-.8"}],["path",{d:"M14 4.1 12 6"}],["path",{d:"m6 12-1.9 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l6=["svg",o,[["path",{d:"M5 3a2 2 0 0 0-2 2"}],["path",{d:"M19 3a2 2 0 0 1 2 2"}],["path",{d:"m12 12 4 10 1.7-4.3L22 16Z"}],["path",{d:"M5 21a2 2 0 0 1-2-2"}],["path",{d:"M9 3h1"}],["path",{d:"M9 21h2"}],["path",{d:"M14 3h1"}],["path",{d:"M3 9v1"}],["path",{d:"M21 9v2"}],["path",{d:"M3 14v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gs=["svg",o,[["path",{d:"M21 11V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"}],["path",{d:"m12 12 4 10 1.7-4.3L22 16Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d6=["svg",o,[["path",{d:"m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z"}],["path",{d:"m13 13 6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p6=["svg",o,[["rect",{x:"5",y:"2",width:"14",height:"20",rx:"7"}],["path",{d:"M12 6v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xs=["svg",o,[["path",{d:"M5 3v16h16"}],["path",{d:"m5 19 6-6"}],["path",{d:"m2 6 3-3 3 3"}],["path",{d:"m18 16 3 3-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g6=["svg",o,[["polyline",{points:"5 11 5 5 11 5"}],["polyline",{points:"19 13 19 19 13 19"}],["line",{x1:"5",x2:"19",y1:"5",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u6=["svg",o,[["polyline",{points:"13 5 19 5 19 11"}],["polyline",{points:"11 19 5 19 5 13"}],["line",{x1:"19",x2:"5",y1:"5",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f6=["svg",o,[["path",{d:"M11 19H5V13"}],["path",{d:"M19 5L5 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v6=["svg",o,[["path",{d:"M19 13V19H13"}],["path",{d:"M5 5L19 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x6=["svg",o,[["path",{d:"M8 18L12 22L16 18"}],["path",{d:"M12 2V22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m6=["svg",o,[["polyline",{points:"18 8 22 12 18 16"}],["polyline",{points:"6 8 2 12 6 16"}],["line",{x1:"2",x2:"22",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M6=["svg",o,[["path",{d:"M6 8L2 12L6 16"}],["path",{d:"M2 12H22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y6=["svg",o,[["path",{d:"M18 8L22 12L18 16"}],["path",{d:"M2 12H22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b6=["svg",o,[["path",{d:"M5 11V5H11"}],["path",{d:"M5 5L19 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w6=["svg",o,[["path",{d:"M13 5H19V11"}],["path",{d:"M19 5L5 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _6=["svg",o,[["path",{d:"M8 6L12 2L16 6"}],["path",{d:"M12 2V22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k6=["svg",o,[["polyline",{points:"8 18 12 22 16 18"}],["polyline",{points:"8 6 12 2 16 6"}],["line",{x1:"12",x2:"12",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C6=["svg",o,[["polyline",{points:"5 9 2 12 5 15"}],["polyline",{points:"9 5 12 2 15 5"}],["polyline",{points:"15 19 12 22 9 19"}],["polyline",{points:"19 9 22 12 19 15"}],["line",{x1:"2",x2:"22",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S6=["svg",o,[["circle",{cx:"8",cy:"18",r:"4"}],["path",{d:"M12 18V2l7 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L6=["svg",o,[["circle",{cx:"12",cy:"18",r:"4"}],["path",{d:"M16 18V2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A6=["svg",o,[["path",{d:"M9 18V5l12-2v13"}],["path",{d:"m9 9 12-2"}],["circle",{cx:"6",cy:"18",r:"3"}],["circle",{cx:"18",cy:"16",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H6=["svg",o,[["path",{d:"M9 18V5l12-2v13"}],["circle",{cx:"6",cy:"18",r:"3"}],["circle",{cx:"18",cy:"16",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V6=["svg",o,[["path",{d:"M9.31 9.31 5 21l7-4 7 4-1.17-3.17"}],["path",{d:"M14.53 8.88 12 2l-1.17 3.17"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P6=["svg",o,[["polygon",{points:"12 2 19 21 12 17 5 21 12 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D6=["svg",o,[["path",{d:"M8.43 8.43 3 11l8 2 2 8 2.57-5.43"}],["path",{d:"M17.39 11.73 22 2l-9.73 4.61"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F6=["svg",o,[["polygon",{points:"3 11 22 2 13 21 11 13 3 11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T6=["svg",o,[["rect",{x:"16",y:"16",width:"6",height:"6",rx:"1"}],["rect",{x:"2",y:"16",width:"6",height:"6",rx:"1"}],["rect",{x:"9",y:"2",width:"6",height:"6",rx:"1"}],["path",{d:"M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"}],["path",{d:"M12 12V8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B6=["svg",o,[["path",{d:"M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"}],["path",{d:"M18 14h-8"}],["path",{d:"M15 18h-5"}],["path",{d:"M10 6h8v4h-8V6Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O6=["svg",o,[["path",{d:"M6 8.32a7.43 7.43 0 0 1 0 7.36"}],["path",{d:"M9.46 6.21a11.76 11.76 0 0 1 0 11.58"}],["path",{d:"M12.91 4.1a15.91 15.91 0 0 1 .01 15.8"}],["path",{d:"M16.37 2a20.16 20.16 0 0 1 0 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E6=["svg",o,[["path",{d:"M12 4V2"}],["path",{d:"M5 10v4a7.004 7.004 0 0 0 5.277 6.787c.412.104.802.292 1.102.592L12 22l.621-.621c.3-.3.69-.488 1.102-.592a7.01 7.01 0 0 0 4.125-2.939"}],["path",{d:"M19 10v3.343"}],["path",{d:"M12 12c-1.349-.573-1.905-1.005-2.5-2-.546.902-1.048 1.353-2.5 2-1.018-.644-1.46-1.08-2-2-1.028.71-1.69.918-3 1 1.081-1.048 1.757-2.03 2-3 .194-.776.84-1.551 1.79-2.21m11.654 5.997c.887-.457 1.28-.891 1.556-1.787 1.032.916 1.683 1.157 3 1-1.297-1.036-1.758-2.03-2-3-.5-2-4-4-8-4-.74 0-1.461.068-2.15.192"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R6=["svg",o,[["path",{d:"M12 4V2"}],["path",{d:"M5 10v4a7.004 7.004 0 0 0 5.277 6.787c.412.104.802.292 1.102.592L12 22l.621-.621c.3-.3.69-.488 1.102-.592A7.003 7.003 0 0 0 19 14v-4"}],["path",{d:"M12 4C8 4 4.5 6 4 8c-.243.97-.919 1.952-2 3 1.31-.082 1.972-.29 3-1 .54.92.982 1.356 2 2 1.452-.647 1.954-1.098 2.5-2 .595.995 1.151 1.427 2.5 2 1.31-.621 1.862-1.058 2.5-2 .629.977 1.162 1.423 2.5 2 1.209-.548 1.68-.967 2-2 1.032.916 1.683 1.157 3 1-1.297-1.036-1.758-2.03-2-3-.5-2-4-4-8-4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z6=["svg",o,[["polygon",{points:"7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I6=["svg",o,[["path",{d:"M3 3h6l6 18h6"}],["path",{d:"M14 3h7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $6=["svg",o,[["circle",{cx:"12",cy:"12",r:"3"}],["circle",{cx:"19",cy:"5",r:"2"}],["circle",{cx:"5",cy:"19",r:"2"}],["path",{d:"M10.4 21.9a10 10 0 0 0 9.941-15.416"}],["path",{d:"M13.5 2.1a10 10 0 0 0-9.841 15.416"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z6=["svg",o,[["polyline",{points:"7 8 3 12 7 16"}],["line",{x1:"21",x2:"11",y1:"12",y2:"12"}],["line",{x1:"21",x2:"11",y1:"6",y2:"6"}],["line",{x1:"21",x2:"11",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W6=["svg",o,[["path",{d:"M3 9h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9Z"}],["path",{d:"m3 9 2.45-4.9A2 2 0 0 1 7.24 3h9.52a2 2 0 0 1 1.8 1.1L21 9"}],["path",{d:"M12 3v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N6=["svg",o,[["path",{d:"m16 16 2 2 4-4"}],["path",{d:"M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"}],["path",{d:"m7.5 4.27 9 5.15"}],["polyline",{points:"3.29 7 12 12 20.71 7"}],["line",{x1:"12",x2:"12",y1:"22",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j6=["svg",o,[["path",{d:"M16 16h6"}],["path",{d:"M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"}],["path",{d:"m7.5 4.27 9 5.15"}],["polyline",{points:"3.29 7 12 12 20.71 7"}],["line",{x1:"12",x2:"12",y1:"22",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U6=["svg",o,[["path",{d:"M20.91 8.84 8.56 2.23a1.93 1.93 0 0 0-1.81 0L3.1 4.13a2.12 2.12 0 0 0-.05 3.69l12.22 6.93a2 2 0 0 0 1.94 0L21 12.51a2.12 2.12 0 0 0-.09-3.67Z"}],["path",{d:"m3.09 8.84 12.35-6.61a1.93 1.93 0 0 1 1.81 0l3.65 1.9a2.12 2.12 0 0 1 .1 3.69L8.73 14.75a2 2 0 0 1-1.94 0L3 12.51a2.12 2.12 0 0 1 .09-3.67Z"}],["line",{x1:"12",x2:"12",y1:"22",y2:"13"}],["path",{d:"M20 13.5v3.37a2.06 2.06 0 0 1-1.11 1.83l-6 3.08a1.93 1.93 0 0 1-1.78 0l-6-3.08A2.06 2.06 0 0 1 4 16.87V13.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q6=["svg",o,[["path",{d:"M16 16h6"}],["path",{d:"M19 13v6"}],["path",{d:"M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"}],["path",{d:"m7.5 4.27 9 5.15"}],["polyline",{points:"3.29 7 12 12 20.71 7"}],["line",{x1:"12",x2:"12",y1:"22",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G6=["svg",o,[["path",{d:"M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"}],["path",{d:"m7.5 4.27 9 5.15"}],["polyline",{points:"3.29 7 12 12 20.71 7"}],["line",{x1:"12",x2:"12",y1:"22",y2:"12"}],["circle",{cx:"18.5",cy:"15.5",r:"2.5"}],["path",{d:"M20.27 17.27 22 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X6=["svg",o,[["path",{d:"M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"}],["path",{d:"m7.5 4.27 9 5.15"}],["polyline",{points:"3.29 7 12 12 20.71 7"}],["line",{x1:"12",x2:"12",y1:"22",y2:"12"}],["path",{d:"m17 13 5 5m-5 0 5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y6=["svg",o,[["path",{d:"m7.5 4.27 9 5.15"}],["path",{d:"M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"}],["path",{d:"m3.3 7 8.7 5 8.7-5"}],["path",{d:"M12 22V12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K6=["svg",o,[["path",{d:"m19 11-8-8-8.6 8.6a2 2 0 0 0 0 2.8l5.2 5.2c.8.8 2 .8 2.8 0L19 11Z"}],["path",{d:"m5 2 5 5"}],["path",{d:"M2 13h15"}],["path",{d:"M22 20a2 2 0 1 1-4 0c0-1.6 1.7-2.4 2-4 .3 1.6 2 2.4 2 4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J6=["svg",o,[["path",{d:"M14 19.9V16h3a2 2 0 0 0 2-2v-2H5v2c0 1.1.9 2 2 2h3v3.9a2 2 0 1 0 4 0Z"}],["path",{d:"M6 12V2h12v10"}],["path",{d:"M14 2v4"}],["path",{d:"M10 2v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q6=["svg",o,[["path",{d:"M18.37 2.63 14 7l-1.59-1.59a2 2 0 0 0-2.82 0L8 7l9 9 1.59-1.59a2 2 0 0 0 0-2.82L17 10l4.37-4.37a2.12 2.12 0 1 0-3-3Z"}],["path",{d:"M9 8c-2 3-4 3.5-7 4l8 10c2-1 6-5 6-7"}],["path",{d:"M14.5 17.5 4.5 15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tv=["svg",o,[["circle",{cx:"13.5",cy:"6.5",r:".5"}],["circle",{cx:"17.5",cy:"10.5",r:".5"}],["circle",{cx:"8.5",cy:"7.5",r:".5"}],["circle",{cx:"6.5",cy:"12.5",r:".5"}],["path",{d:"M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ev=["svg",o,[["path",{d:"M13 8c0-2.76-2.46-5-5.5-5S2 5.24 2 8h2l1-1 1 1h4"}],["path",{d:"M13 7.14A5.82 5.82 0 0 1 16.5 6c3.04 0 5.5 2.24 5.5 5h-3l-1-1-1 1h-3"}],["path",{d:"M5.89 9.71c-2.15 2.15-2.3 5.47-.35 7.43l4.24-4.25.7-.7.71-.71 2.12-2.12c-1.95-1.96-5.27-1.8-7.42.35z"}],["path",{d:"M11 15.5c.5 2.5-.17 4.5-1 6.5h4c2-5.5-.5-12-1-14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"15",y2:"15"}],["path",{d:"m15 8-3 3-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const av=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M14 15h1"}],["path",{d:"M19 15h2"}],["path",{d:"M3 15h2"}],["path",{d:"M9 15h1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const iv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"15",y2:"15"}],["path",{d:"m9 10 3-3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"15",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ys=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ov=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 14v1"}],["path",{d:"M9 19v2"}],["path",{d:"M9 3v2"}],["path",{d:"M9 9v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ks=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m14 9 3 3-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Js=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"9",x2:"9",y1:"3",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"15",x2:"15",y1:"3",y2:"21"}],["path",{d:"m8 9 3 3-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M15 14v1"}],["path",{d:"M15 19v2"}],["path",{d:"M15 3v2"}],["path",{d:"M15 9v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"15",x2:"15",y1:"3",y2:"21"}],["path",{d:"m10 15-3-3 3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"15",x2:"15",y1:"3",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"9",y2:"9"}],["path",{d:"m9 16 3-3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M14 9h1"}],["path",{d:"M19 9h2"}],["path",{d:"M3 9h2"}],["path",{d:"M9 9h1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"9",y2:"9"}],["path",{d:"m15 14-3 3-3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"9",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fv=["svg",o,[["path",{d:"m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vv=["svg",o,[["path",{d:"M8 21s-4-3-4-9 4-9 4-9"}],["path",{d:"M16 3s4 3 4 9-4 9-4 9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xv=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m5 5 14 14"}],["path",{d:"M13 13a3 3 0 1 0 0-6H9v2"}],["path",{d:"M9 17v-2.34"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mv=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9 17V7h4a3 3 0 0 1 0 6H9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mv=["svg",o,[["path",{d:"M9 9a3 3 0 1 1 6 0"}],["path",{d:"M12 12v3"}],["path",{d:"M11 15h2"}],["path",{d:"M19 9a7 7 0 1 0-13.6 2.3C6.4 14.4 8 19 8 19h8s1.6-4.6 2.6-7.7c.3-.8.4-1.5.4-2.3"}],["path",{d:"M12 19v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yv=["svg",o,[["path",{d:"M3.6 3.6A2 2 0 0 1 5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-.59 1.41"}],["path",{d:"M3 8.7V19a2 2 0 0 0 2 2h10.3"}],["path",{d:"m2 2 20 20"}],["path",{d:"M13 13a3 3 0 1 0 0-6H9v2"}],["path",{d:"M9 17v-2.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 17V7h4a3 3 0 0 1 0 6H9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wv=["svg",o,[["path",{d:"M5.8 11.3 2 22l10.7-3.79"}],["path",{d:"M4 3h.01"}],["path",{d:"M22 8h.01"}],["path",{d:"M15 2h.01"}],["path",{d:"M22 20h.01"}],["path",{d:"m22 2-2.24.75a2.9 2.9 0 0 0-1.96 3.12v0c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10"}],["path",{d:"m22 13-.82-.33c-.86-.34-1.82.2-1.98 1.11v0c-.11.7-.72 1.22-1.43 1.22H17"}],["path",{d:"m11 2 .33.82c.34.86-.2 1.82-1.11 1.98v0C9.52 4.9 9 5.52 9 6.23V7"}],["path",{d:"M11 13c1.93 1.93 2.83 4.17 2 5-.83.83-3.07-.07-5-2-1.93-1.93-2.83-4.17-2-5 .83-.83 3.07.07 5 2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _v=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"10",x2:"10",y1:"15",y2:"9"}],["line",{x1:"14",x2:"14",y1:"15",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kv=["svg",o,[["path",{d:"M10 15V9"}],["path",{d:"M14 15V9"}],["path",{d:"M7.714 2h8.572L22 7.714v8.572L16.286 22H7.714L2 16.286V7.714L7.714 2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cv=["svg",o,[["rect",{width:"4",height:"16",x:"6",y:"4"}],["rect",{width:"4",height:"16",x:"14",y:"4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sv=["svg",o,[["circle",{cx:"11",cy:"4",r:"2"}],["circle",{cx:"18",cy:"8",r:"2"}],["circle",{cx:"20",cy:"16",r:"2"}],["path",{d:"M9 10a5 5 0 0 1 5 5v3.5a3.5 3.5 0 0 1-6.84 1.045Q6.52 17.48 4.46 16.84A3.5 3.5 0 0 1 5.5 10Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lv=["svg",o,[["rect",{width:"14",height:"20",x:"5",y:"2",rx:"2"}],["path",{d:"M15 14h.01"}],["path",{d:"M9 6h6"}],["path",{d:"M9 10h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qs=["svg",o,[["path",{d:"M12 20h9"}],["path",{d:"M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V1=["svg",o,[["path",{d:"M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"}],["path",{d:"M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Av=["svg",o,[["path",{d:"m12 19 7-7 3 3-7 7-3-3z"}],["path",{d:"m18 13-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"}],["path",{d:"m2 2 7.586 7.586"}],["circle",{cx:"11",cy:"11",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ta=["svg",o,[["path",{d:"M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hv=["svg",o,[["path",{d:"M12 20h9"}],["path",{d:"M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"}],["path",{d:"m15 5 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vv=["svg",o,[["path",{d:"m15 5 4 4"}],["path",{d:"M13 7 8.7 2.7a2.41 2.41 0 0 0-3.4 0L2.7 5.3a2.41 2.41 0 0 0 0 3.4L7 13"}],["path",{d:"m8 6 2-2"}],["path",{d:"m2 22 5.5-1.5L21.17 6.83a2.82 2.82 0 0 0-4-4L3.5 16.5Z"}],["path",{d:"m18 16 2-2"}],["path",{d:"m17 11 4.3 4.3c.94.94.94 2.46 0 3.4l-2.6 2.6c-.94.94-2.46.94-3.4 0L11 17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pv=["svg",o,[["path",{d:"M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"}],["path",{d:"m15 5 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dv=["svg",o,[["path",{d:"M3.5 8.7c-.7.5-1 1.4-.7 2.2l2.8 8.7c.3.8 1 1.4 1.9 1.4h9.1c.9 0 1.6-.6 1.9-1.4l2.8-8.7c.3-.8 0-1.7-.7-2.2l-7.4-5.3a2.1 2.1 0 0 0-2.4 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fv=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m15 9-6 6"}],["path",{d:"M9 9h.01"}],["path",{d:"M15 15h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tv=["svg",o,[["path",{d:"M2.7 10.3a2.41 2.41 0 0 0 0 3.41l7.59 7.59a2.41 2.41 0 0 0 3.41 0l7.59-7.59a2.41 2.41 0 0 0 0-3.41L13.7 2.71a2.41 2.41 0 0 0-3.41 0Z"}],["path",{d:"M9.2 9.2h.01"}],["path",{d:"m14.5 9.5-5 5"}],["path",{d:"M14.7 14.8h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m15 9-6 6"}],["path",{d:"M9 9h.01"}],["path",{d:"M15 15h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ov=["svg",o,[["line",{x1:"19",x2:"5",y1:"5",y2:"19"}],["circle",{cx:"6.5",cy:"6.5",r:"2.5"}],["circle",{cx:"17.5",cy:"17.5",r:"2.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ev=["svg",o,[["circle",{cx:"12",cy:"5",r:"1"}],["path",{d:"m9 20 3-6 3 6"}],["path",{d:"m6 8 6 2 6-2"}],["path",{d:"M12 10v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rv=["svg",o,[["path",{d:"M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"}],["path",{d:"M14.05 2a9 9 0 0 1 8 7.94"}],["path",{d:"M14.05 6A5 5 0 0 1 18 10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zv=["svg",o,[["polyline",{points:"18 2 22 6 18 10"}],["line",{x1:"14",x2:"22",y1:"6",y2:"6"}],["path",{d:"M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Iv=["svg",o,[["polyline",{points:"16 2 16 8 22 8"}],["line",{x1:"22",x2:"16",y1:"2",y2:"8"}],["path",{d:"M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $v=["svg",o,[["line",{x1:"22",x2:"16",y1:"2",y2:"8"}],["line",{x1:"16",x2:"22",y1:"2",y2:"8"}],["path",{d:"M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zv=["svg",o,[["path",{d:"M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.42 19.42 0 0 1-3.33-2.67m-2.67-3.34a19.79 19.79 0 0 1-3.07-8.63A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91"}],["line",{x1:"22",x2:"2",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wv=["svg",o,[["polyline",{points:"22 8 22 2 16 2"}],["line",{x1:"16",x2:"22",y1:"8",y2:"2"}],["path",{d:"M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nv=["svg",o,[["path",{d:"M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M7 7h10"}],["path",{d:"M10 7v10"}],["path",{d:"M16 17a2 2 0 0 1-2-2V7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uv=["svg",o,[["line",{x1:"9",x2:"9",y1:"4",y2:"20"}],["path",{d:"M4 7c0-1.7 1.3-3 3-3h13"}],["path",{d:"M18 20c-1.7 0-3-1.3-3-3V4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qv=["svg",o,[["path",{d:"M18.5 8c-1.4 0-2.6-.8-3.2-2A6.87 6.87 0 0 0 2 9v11a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-8.5C22 9.6 20.4 8 18.5 8"}],["path",{d:"M2 14h20"}],["path",{d:"M6 14v4"}],["path",{d:"M10 14v4"}],["path",{d:"M14 14v4"}],["path",{d:"M18 14v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gv=["svg",o,[["path",{d:"M21 9V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10c0 1.1.9 2 2 2h4"}],["rect",{width:"10",height:"7",x:"12",y:"13",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xv=["svg",o,[["path",{d:"M8 4.5v5H3m-1-6 6 6m13 0v-3c0-1.16-.84-2-2-2h-7m-9 9v2c0 1.05.95 2 2 2h3"}],["rect",{width:"10",height:"7",x:"12",y:"13.5",ry:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yv=["svg",o,[["path",{d:"M21.21 15.89A10 10 0 1 1 8 2.83"}],["path",{d:"M22 12A10 10 0 0 0 12 2v10z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kv=["svg",o,[["path",{d:"M19 5c-1.5 0-2.8 1.4-3 2-3.5-1.5-11-.3-11 5 0 1.8 0 3 2 4.5V20h4v-2h3v2h4v-4c1-.5 1.7-1 2-2h2v-4h-2c0-1-.5-1.5-1-2h0V5z"}],["path",{d:"M2 9v1c0 1.1.9 2 2 2h1"}],["path",{d:"M16 11h0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jv=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M12 12H9.5a2.5 2.5 0 0 1 0-5H17"}],["path",{d:"M12 7v10"}],["path",{d:"M16 7v10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qv=["svg",o,[["path",{d:"M13 4v16"}],["path",{d:"M17 4v16"}],["path",{d:"M19 4H9.5a4.5 4.5 0 0 0 0 9H13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t8=["svg",o,[["path",{d:"m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"}],["path",{d:"m8.5 8.5 7 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e8=["svg",o,[["line",{x1:"2",x2:"22",y1:"2",y2:"22"}],["line",{x1:"12",x2:"12",y1:"17",y2:"22"}],["path",{d:"M9 9v1.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V17h12"}],["path",{d:"M15 9.34V6h1a2 2 0 0 0 0-4H7.89"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s8=["svg",o,[["line",{x1:"12",x2:"12",y1:"17",y2:"22"}],["path",{d:"M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a8=["svg",o,[["path",{d:"m2 22 1-1h3l9-9"}],["path",{d:"M3 21v-3l9-9"}],["path",{d:"m15 6 3.4-3.4a2.1 2.1 0 1 1 3 3L18 9l.4.4a2.1 2.1 0 1 1-3 3l-3.8-3.8a2.1 2.1 0 1 1 3-3l.4.4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i8=["svg",o,[["path",{d:"M15 11h.01"}],["path",{d:"M11 15h.01"}],["path",{d:"M16 16h.01"}],["path",{d:"m2 16 20 6-6-20A20 20 0 0 0 2 16"}],["path",{d:"M5.71 17.11a17.04 17.04 0 0 1 11.4-11.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n8=["svg",o,[["path",{d:"M2 22h20"}],["path",{d:"M3.77 10.77 2 9l2-4.5 1.1.55c.55.28.9.84.9 1.45s.35 1.17.9 1.45L8 8.5l3-6 1.05.53a2 2 0 0 1 1.09 1.52l.72 5.4a2 2 0 0 0 1.09 1.52l4.4 2.2c.42.22.78.55 1.01.96l.6 1.03c.49.88-.06 1.98-1.06 2.1l-1.18.15c-.47.06-.95-.02-1.37-.24L4.29 11.15a2 2 0 0 1-.52-.38Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o8=["svg",o,[["path",{d:"M2 22h20"}],["path",{d:"M6.36 17.4 4 17l-2-4 1.1-.55a2 2 0 0 1 1.8 0l.17.1a2 2 0 0 0 1.8 0L8 12 5 6l.9-.45a2 2 0 0 1 2.09.2l4.02 3a2 2 0 0 0 2.1.2l4.19-2.06a2.41 2.41 0 0 1 1.73-.17L21 7a1.4 1.4 0 0 1 .87 1.99l-.38.76c-.23.46-.6.84-1.07 1.08L7.58 17.2a2 2 0 0 1-1.22.18Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r8=["svg",o,[["path",{d:"M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h8=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["polygon",{points:"10 8 16 12 10 16 10 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c8=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m9 8 6 4-6 4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l8=["svg",o,[["polygon",{points:"5 3 19 12 5 21 5 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d8=["svg",o,[["path",{d:"M9 2v6"}],["path",{d:"M15 2v6"}],["path",{d:"M12 17v5"}],["path",{d:"M5 8h14"}],["path",{d:"M6 11V8h12v3a6 6 0 1 1-12 0v0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p8=["svg",o,[["path",{d:"m13 2-2 2.5h3L12 7"}],["path",{d:"M10 14v-3"}],["path",{d:"M14 14v-3"}],["path",{d:"M11 19c-1.7 0-3-1.3-3-3v-2h8v2c0 1.7-1.3 3-3 3Z"}],["path",{d:"M12 22v-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g8=["svg",o,[["path",{d:"M6.3 20.3a2.4 2.4 0 0 0 3.4 0L12 18l-6-6-2.3 2.3a2.4 2.4 0 0 0 0 3.4Z"}],["path",{d:"m2 22 3-3"}],["path",{d:"M7.5 13.5 10 11"}],["path",{d:"M10.5 16.5 13 14"}],["path",{d:"m18 3-4 4h6l-4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u8=["svg",o,[["path",{d:"M12 22v-5"}],["path",{d:"M9 8V2"}],["path",{d:"M15 8V2"}],["path",{d:"M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f8=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M8 12h8"}],["path",{d:"M12 8v8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v8=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M8 12h8"}],["path",{d:"M12 8v8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x8=["svg",o,[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m8=["svg",o,[["path",{d:"M3 2v1c0 1 2 1 2 2S3 6 3 7s2 1 2 2-2 1-2 2 2 1 2 2"}],["path",{d:"M18 6h.01"}],["path",{d:"M6 18h.01"}],["path",{d:"M20.83 8.83a4 4 0 0 0-5.66-5.66l-12 12a4 4 0 1 0 5.66 5.66Z"}],["path",{d:"M18 11.66V22a4 4 0 0 0 4-4V6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M8=["svg",o,[["path",{d:"M4 3h16a2 2 0 0 1 2 2v6a10 10 0 0 1-10 10A10 10 0 0 1 2 11V5a2 2 0 0 1 2-2z"}],["polyline",{points:"8 10 12 14 16 10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y8=["svg",o,[["circle",{cx:"12",cy:"11",r:"1"}],["path",{d:"M11 17a1 1 0 0 1 2 0c0 .5-.34 3-.5 4.5a.5.5 0 0 1-1 0c-.16-1.5-.5-4-.5-4.5Z"}],["path",{d:"M8 14a5 5 0 1 1 8 0"}],["path",{d:"M17 18.5a9 9 0 1 0-10 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b8=["svg",o,[["path",{d:"M22 14a8 8 0 0 1-8 8"}],["path",{d:"M18 11v-1a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"}],["path",{d:"M14 10V9a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v1"}],["path",{d:"M10 9.5V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v10"}],["path",{d:"M18 11a2 2 0 1 1 4 0v3a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w8=["svg",o,[["path",{d:"M18 8a2 2 0 0 0 0-4 2 2 0 0 0-4 0 2 2 0 0 0-4 0 2 2 0 0 0-4 0 2 2 0 0 0 0 4"}],["path",{d:"M10 22 9 8"}],["path",{d:"m14 22 1-14"}],["path",{d:"M20 8c.5 0 .9.4.8 1l-2.6 12c-.1.5-.7 1-1.2 1H7c-.6 0-1.1-.4-1.2-1L3.2 9c-.1-.6.3-1 .8-1Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _8=["svg",o,[["path",{d:"M18.6 14.4c.8-.8.8-2 0-2.8l-8.1-8.1a4.95 4.95 0 1 0-7.1 7.1l8.1 8.1c.9.7 2.1.7 2.9-.1Z"}],["path",{d:"m22 22-5.5-5.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k8=["svg",o,[["path",{d:"M18 7c0-5.333-8-5.333-8 0"}],["path",{d:"M10 7v14"}],["path",{d:"M6 21h12"}],["path",{d:"M6 13h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C8=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 12V6"}],["path",{d:"M8 7.5A6.1 6.1 0 0 0 12 18a6 6 0 0 0 4-10.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S8=["svg",o,[["path",{d:"M18.36 6.64A9 9 0 0 1 20.77 15"}],["path",{d:"M6.16 6.16a9 9 0 1 0 12.68 12.68"}],["path",{d:"M12 2v4"}],["path",{d:"m2 2 20 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L8=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M12 7v5"}],["path",{d:"M8 9a5.14 5.14 0 0 0 4 8 4.95 4.95 0 0 0 4-8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A8=["svg",o,[["path",{d:"M12 2v10"}],["path",{d:"M18.4 6.6a9 9 0 1 1-12.77.04"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H8=["svg",o,[["path",{d:"M2 3h20"}],["path",{d:"M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"}],["path",{d:"m7 21 5-5 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V8=["svg",o,[["polyline",{points:"6 9 6 2 18 2 18 9"}],["path",{d:"M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"}],["rect",{width:"12",height:"8",x:"6",y:"14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P8=["svg",o,[["path",{d:"M5 7 3 5"}],["path",{d:"M9 6V3"}],["path",{d:"m13 7 2-2"}],["circle",{cx:"9",cy:"13",r:"3"}],["path",{d:"M11.83 12H20a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h2.17"}],["path",{d:"M16 16h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D8=["svg",o,[["path",{d:"M19.439 7.85c-.049.322.059.648.289.878l1.568 1.568c.47.47.706 1.087.706 1.704s-.235 1.233-.706 1.704l-1.611 1.611a.98.98 0 0 1-.837.276c-.47-.07-.802-.48-.968-.925a2.501 2.501 0 1 0-3.214 3.214c.446.166.855.497.925.968a.979.979 0 0 1-.276.837l-1.61 1.61a2.404 2.404 0 0 1-1.705.707 2.402 2.402 0 0 1-1.704-.706l-1.568-1.568a1.026 1.026 0 0 0-.877-.29c-.493.074-.84.504-1.02.968a2.5 2.5 0 1 1-3.237-3.237c.464-.18.894-.527.967-1.02a1.026 1.026 0 0 0-.289-.877l-1.568-1.568A2.402 2.402 0 0 1 1.998 12c0-.617.236-1.234.706-1.704L4.23 8.77c.24-.24.581-.353.917-.303.515.077.877.528 1.073 1.01a2.5 2.5 0 1 0 3.259-3.259c-.482-.196-.933-.558-1.01-1.073-.05-.336.062-.676.303-.917l1.525-1.525A2.402 2.402 0 0 1 12 1.998c.617 0 1.234.236 1.704.706l1.568 1.568c.23.23.556.338.877.29.493-.074.84-.504 1.02-.968a2.5 2.5 0 1 1 3.237 3.237c-.464.18-.894.527-.967 1.02Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F8=["svg",o,[["path",{d:"M2.5 16.88a1 1 0 0 1-.32-1.43l9-13.02a1 1 0 0 1 1.64 0l9 13.01a1 1 0 0 1-.32 1.44l-8.51 4.86a2 2 0 0 1-1.98 0Z"}],["path",{d:"M12 2v20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T8=["svg",o,[["rect",{width:"5",height:"5",x:"3",y:"3",rx:"1"}],["rect",{width:"5",height:"5",x:"16",y:"3",rx:"1"}],["rect",{width:"5",height:"5",x:"3",y:"16",rx:"1"}],["path",{d:"M21 16h-3a2 2 0 0 0-2 2v3"}],["path",{d:"M21 21v.01"}],["path",{d:"M12 7v3a2 2 0 0 1-2 2H7"}],["path",{d:"M3 12h.01"}],["path",{d:"M12 3h.01"}],["path",{d:"M12 16v.01"}],["path",{d:"M16 12h1"}],["path",{d:"M21 12v.01"}],["path",{d:"M12 21v-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B8=["svg",o,[["path",{d:"M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"}],["path",{d:"M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O8=["svg",o,[["path",{d:"M20 8.54V4a2 2 0 1 0-4 0v3"}],["path",{d:"M18 21h-8a4 4 0 0 1-4-4 7 7 0 0 1 7-7h.2L9.6 6.4a1.93 1.93 0 1 1 2.8-2.8L15.8 7h.2c3.3 0 6 2.7 6 6v1a2 2 0 0 1-2 2h-1c-1.7 0-3 1.3-3 3"}],["path",{d:"M7.61 12.53a3 3 0 1 0-1.6 4.3"}],["path",{d:"M13 16a3 3 0 0 1 2.24 5"}],["path",{d:"M18 12h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E8=["svg",o,[["path",{d:"M19.07 4.93A10 10 0 0 0 6.99 3.34"}],["path",{d:"M4 6h.01"}],["path",{d:"M2.29 9.62A10 10 0 1 0 21.31 8.35"}],["path",{d:"M16.24 7.76A6 6 0 1 0 8.23 16.67"}],["path",{d:"M12 18h.01"}],["path",{d:"M17.99 11.66A6 6 0 0 1 15.77 16.67"}],["circle",{cx:"12",cy:"12",r:"2"}],["path",{d:"m13.41 10.59 5.66-5.66"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R8=["svg",o,[["path",{d:"M12 12h0.01"}],["path",{d:"M7.5 4.2c-.3-.5-.9-.7-1.3-.4C3.9 5.5 2.3 8.1 2 11c-.1.5.4 1 1 1h5c0-1.5.8-2.8 2-3.4-1.1-1.9-2-3.5-2.5-4.4z"}],["path",{d:"M21 12c.6 0 1-.4 1-1-.3-2.9-1.8-5.5-4.1-7.1-.4-.3-1.1-.2-1.3.3-.6.9-1.5 2.5-2.6 4.3 1.2.7 2 2 2 3.5h5z"}],["path",{d:"M7.5 19.8c-.3.5-.1 1.1.4 1.3 2.6 1.2 5.6 1.2 8.2 0 .5-.2.7-.8.4-1.3-.5-.9-1.4-2.5-2.5-4.3-1.2.7-2.8.7-4 0-1.1 1.8-2 3.4-2.5 4.3z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z8=["svg",o,[["path",{d:"M5 16v2"}],["path",{d:"M19 16v2"}],["rect",{width:"20",height:"8",x:"2",y:"8",rx:"2"}],["path",{d:"M18 12h0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I8=["svg",o,[["path",{d:"M4.9 16.1C1 12.2 1 5.8 4.9 1.9"}],["path",{d:"M7.8 4.7a6.14 6.14 0 0 0-.8 7.5"}],["circle",{cx:"12",cy:"9",r:"2"}],["path",{d:"M16.2 4.8c2 2 2.26 5.11.8 7.47"}],["path",{d:"M19.1 1.9a9.96 9.96 0 0 1 0 14.1"}],["path",{d:"M9.5 18h5"}],["path",{d:"m8 22 4-11 4 11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $8=["svg",o,[["path",{d:"M4.9 19.1C1 15.2 1 8.8 4.9 4.9"}],["path",{d:"M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"}],["circle",{cx:"12",cy:"12",r:"2"}],["path",{d:"M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"}],["path",{d:"M19.1 4.9C23 8.8 23 15.1 19.1 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z8=["svg",o,[["path",{d:"M20.34 17.52a10 10 0 1 0-2.82 2.82"}],["circle",{cx:"19",cy:"19",r:"2"}],["path",{d:"m13.41 13.41 4.18 4.18"}],["circle",{cx:"12",cy:"12",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W8=["svg",o,[["path",{d:"M5 15h14"}],["path",{d:"M5 9h14"}],["path",{d:"m14 20-5-5 6-6-5-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N8=["svg",o,[["path",{d:"M22 17a10 10 0 0 0-20 0"}],["path",{d:"M6 17a6 6 0 0 1 12 0"}],["path",{d:"M10 17a2 2 0 0 1 4 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j8=["svg",o,[["path",{d:"M17 5c0-1.7-1.3-3-3-3s-3 1.3-3 3c0 .8.3 1.5.8 2H11c-3.9 0-7 3.1-7 7v0c0 2.2 1.8 4 4 4"}],["path",{d:"M16.8 3.9c.3-.3.6-.5 1-.7 1.5-.6 3.3.1 3.9 1.6.6 1.5-.1 3.3-1.6 3.9l1.6 2.8c.2.3.2.7.2 1-.2.8-.9 1.2-1.7 1.1 0 0-1.6-.3-2.7-.6H17c-1.7 0-3 1.3-3 3"}],["path",{d:"M13.2 18a3 3 0 0 0-2.2-5"}],["path",{d:"M13 22H4a2 2 0 0 1 0-4h12"}],["path",{d:"M16 9h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U8=["svg",o,[["rect",{width:"12",height:"20",x:"6",y:"2",rx:"2"}],["rect",{width:"20",height:"12",x:"2",y:"6",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q8=["svg",o,[["path",{d:"M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1-2-1Z"}],["path",{d:"M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"}],["path",{d:"M12 17V7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G8=["svg",o,[["rect",{width:"20",height:"12",x:"2",y:"6",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X8=["svg",o,[["rect",{width:"12",height:"20",x:"6",y:"2",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y8=["svg",o,[["path",{d:"M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"}],["path",{d:"M11 19h8.203a1.83 1.83 0 0 0 1.556-.89 1.784 1.784 0 0 0 0-1.775l-1.226-2.12"}],["path",{d:"m14 16-3 3 3 3"}],["path",{d:"M8.293 13.596 7.196 9.5 3.1 10.598"}],["path",{d:"m9.344 5.811 1.093-1.892A1.83 1.83 0 0 1 11.985 3a1.784 1.784 0 0 1 1.546.888l3.943 6.843"}],["path",{d:"m13.378 9.633 4.096 1.098 1.097-4.096"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K8=["svg",o,[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5v0A5.5 5.5 0 0 0 9.5 20H13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J8=["svg",o,[["circle",{cx:"12",cy:"17",r:"1"}],["path",{d:"M21 7v6h-6"}],["path",{d:"M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q8=["svg",o,[["path",{d:"M21 7v6h-6"}],["path",{d:"M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tx=["svg",o,[["path",{d:"M3 2v6h6"}],["path",{d:"M21 12A9 9 0 0 0 6 5.3L3 8"}],["path",{d:"M21 22v-6h-6"}],["path",{d:"M3 12a9 9 0 0 0 15 6.7l3-2.7"}],["circle",{cx:"12",cy:"12",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ex=["svg",o,[["path",{d:"M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"}],["path",{d:"M3 3v5h5"}],["path",{d:"M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"}],["path",{d:"M16 16h5v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sx=["svg",o,[["path",{d:"M21 8L18.74 5.74A9.75 9.75 0 0 0 12 3C11 3 10.03 3.16 9.13 3.47"}],["path",{d:"M8 16H3v5"}],["path",{d:"M3 12C3 9.51 4 7.26 5.64 5.64"}],["path",{d:"m3 16 2.26 2.26A9.75 9.75 0 0 0 12 21c2.49 0 4.74-1 6.36-2.64"}],["path",{d:"M21 12c0 1-.16 1.97-.47 2.87"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M22 22 2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ax=["svg",o,[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ix=["svg",o,[["path",{d:"M5 6a4 4 0 0 1 4-4h6a4 4 0 0 1 4 4v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6Z"}],["path",{d:"M5 10h14"}],["path",{d:"M15 7v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nx=["svg",o,[["path",{d:"M17 3v10"}],["path",{d:"m12.67 5.5 8.66 5"}],["path",{d:"m12.67 10.5 8.66-5"}],["path",{d:"M9 17a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ox=["svg",o,[["path",{d:"M4 7V4h16v3"}],["path",{d:"M5 20h6"}],["path",{d:"M13 4 8 20"}],["path",{d:"m15 15 5 5"}],["path",{d:"m20 15-5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rx=["svg",o,[["path",{d:"m17 2 4 4-4 4"}],["path",{d:"M3 11v-1a4 4 0 0 1 4-4h14"}],["path",{d:"m7 22-4-4 4-4"}],["path",{d:"M21 13v1a4 4 0 0 1-4 4H3"}],["path",{d:"M11 10h1v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hx=["svg",o,[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cx=["svg",o,[["path",{d:"m17 2 4 4-4 4"}],["path",{d:"M3 11v-1a4 4 0 0 1 4-4h14"}],["path",{d:"m7 22-4-4 4-4"}],["path",{d:"M21 13v1a4 4 0 0 1-4 4H3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lx=["svg",o,[["path",{d:"M14 4c0-1.1.9-2 2-2"}],["path",{d:"M20 2c1.1 0 2 .9 2 2"}],["path",{d:"M22 8c0 1.1-.9 2-2 2"}],["path",{d:"M16 10c-1.1 0-2-.9-2-2"}],["path",{d:"m3 7 3 3 3-3"}],["path",{d:"M6 10V5c0-1.7 1.3-3 3-3h1"}],["rect",{width:"8",height:"8",x:"2",y:"14",rx:"2"}],["path",{d:"M14 14c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2"}],["path",{d:"M20 14c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dx=["svg",o,[["path",{d:"M14 4c0-1.1.9-2 2-2"}],["path",{d:"M20 2c1.1 0 2 .9 2 2"}],["path",{d:"M22 8c0 1.1-.9 2-2 2"}],["path",{d:"M16 10c-1.1 0-2-.9-2-2"}],["path",{d:"m3 7 3 3 3-3"}],["path",{d:"M6 10V5c0-1.7 1.3-3 3-3h1"}],["rect",{width:"8",height:"8",x:"2",y:"14",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const px=["svg",o,[["polyline",{points:"7 17 2 12 7 7"}],["polyline",{points:"12 17 7 12 12 7"}],["path",{d:"M22 18v-2a4 4 0 0 0-4-4H7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gx=["svg",o,[["polyline",{points:"9 17 4 12 9 7"}],["path",{d:"M20 18v-2a4 4 0 0 0-4-4H4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ux=["svg",o,[["polygon",{points:"11 19 2 12 11 5 11 19"}],["polygon",{points:"22 19 13 12 22 5 22 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fx=["svg",o,[["path",{d:"M17.75 9.01c-.52 2.08-1.83 3.64-3.18 5.49l-2.6 3.54-2.97 4-3.5-2.54 3.85-4.97c-1.86-2.61-2.8-3.77-3.16-5.44"}],["path",{d:"M17.75 9.01A7 7 0 0 0 6.2 9.1C6.06 8.5 6 7.82 6 7c0-3.5 2.83-5 5.98-5C15.24 2 18 3.5 18 7c0 .73-.09 1.4-.25 2.01Z"}],["path",{d:"m9.35 14.53 2.64-3.31"}],["path",{d:"m11.97 18.04 2.99 4 3.54-2.54-3.93-5"}],["path",{d:"M14 8c0 1-1 2-2.01 3.22C11 10 10 9 10 8a2 2 0 1 1 4 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vx=["svg",o,[["path",{d:"M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"}],["path",{d:"m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"}],["path",{d:"M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"}],["path",{d:"M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xx=["svg",o,[["polyline",{points:"3.5 2 6.5 12.5 18 12.5"}],["line",{x1:"9.5",x2:"5.5",y1:"12.5",y2:"20"}],["line",{x1:"15",x2:"18.5",y1:"12.5",y2:"20"}],["path",{d:"M2.75 18a13 13 0 0 0 18.5 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mx=["svg",o,[["path",{d:"M6 19V5"}],["path",{d:"M10 19V6.8"}],["path",{d:"M14 19v-7.8"}],["path",{d:"M18 5v4"}],["path",{d:"M18 19v-6"}],["path",{d:"M22 19V9"}],["path",{d:"M2 19V9a4 4 0 0 1 4-4c2 0 4 1.33 6 4s4 4 6 4a4 4 0 1 0-3-6.65"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ea=["svg",o,[["path",{d:"M16.466 7.5C15.643 4.237 13.952 2 12 2 9.239 2 7 6.477 7 12s2.239 10 5 10c.342 0 .677-.069 1-.2"}],["path",{d:"m15.194 13.707 3.814 1.86-1.86 3.814"}],["path",{d:"M19 15.57c-1.804.885-4.274 1.43-7 1.43-5.523 0-10-2.239-10-5s4.477-5 10-5c4.838 0 8.873 1.718 9.8 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mx=["svg",o,[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"}],["path",{d:"M3 3v5h5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yx=["svg",o,[["path",{d:"M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bx=["svg",o,[["circle",{cx:"6",cy:"19",r:"3"}],["path",{d:"M9 19h8.5c.4 0 .9-.1 1.3-.2"}],["path",{d:"M5.2 5.2A3.5 3.53 0 0 0 6.5 12H12"}],["path",{d:"m2 2 20 20"}],["path",{d:"M21 15.3a3.5 3.5 0 0 0-3.3-3.3"}],["path",{d:"M15 5h-4.3"}],["circle",{cx:"18",cy:"5",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wx=["svg",o,[["circle",{cx:"6",cy:"19",r:"3"}],["path",{d:"M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"}],["circle",{cx:"18",cy:"5",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _x=["svg",o,[["rect",{width:"20",height:"8",x:"2",y:"14",rx:"2"}],["path",{d:"M6.01 18H6"}],["path",{d:"M10.01 18H10"}],["path",{d:"M15 10v4"}],["path",{d:"M17.84 7.17a4 4 0 0 0-5.66 0"}],["path",{d:"M20.66 4.34a8 8 0 0 0-11.31 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kx=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cx=["svg",o,[["path",{d:"M4 11a9 9 0 0 1 9 9"}],["path",{d:"M4 4a16 16 0 0 1 16 16"}],["circle",{cx:"5",cy:"19",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sx=["svg",o,[["path",{d:"M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"}],["path",{d:"m14.5 12.5 2-2"}],["path",{d:"m11.5 9.5 2-2"}],["path",{d:"m8.5 6.5 2-2"}],["path",{d:"m17.5 15.5 2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lx=["svg",o,[["path",{d:"M6 11h8a4 4 0 0 0 0-8H9v18"}],["path",{d:"M6 15h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ax=["svg",o,[["path",{d:"M22 18H2a4 4 0 0 0 4 4h12a4 4 0 0 0 4-4Z"}],["path",{d:"M21 14 10 2 3 14h18Z"}],["path",{d:"M10 2v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hx=["svg",o,[["path",{d:"M7 21h10"}],["path",{d:"M12 21a9 9 0 0 0 9-9H3a9 9 0 0 0 9 9Z"}],["path",{d:"M11.38 12a2.4 2.4 0 0 1-.4-4.77 2.4 2.4 0 0 1 3.2-2.77 2.4 2.4 0 0 1 3.47-.63 2.4 2.4 0 0 1 3.37 3.37 2.4 2.4 0 0 1-1.1 3.7 2.51 2.51 0 0 1 .03 1.1"}],["path",{d:"m13 12 4-4"}],["path",{d:"M10.9 7.25A3.99 3.99 0 0 0 4 10c0 .73.2 1.41.54 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vx=["svg",o,[["path",{d:"M3 11v3a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-3"}],["path",{d:"M12 19H4a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-3.83"}],["path",{d:"m3 11 7.77-6.04a2 2 0 0 1 2.46 0L21 11H3Z"}],["path",{d:"M12.97 19.77 7 15h12.5l-3.75 4.5a2 2 0 0 1-2.78.27Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Px=["svg",o,[["path",{d:"M4 10a7.31 7.31 0 0 0 10 10Z"}],["path",{d:"m9 15 3-3"}],["path",{d:"M17 13a6 6 0 0 0-6-6"}],["path",{d:"M21 13A10 10 0 0 0 11 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dx=["svg",o,[["path",{d:"M13 7 9 3 5 7l4 4"}],["path",{d:"m17 11 4 4-4 4-4-4"}],["path",{d:"m8 12 4 4 6-6-4-4Z"}],["path",{d:"m16 8 3-3"}],["path",{d:"M9 21a6 6 0 0 0-6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fx=["svg",o,[["path",{d:"M6 4a2 2 0 0 1 2-2h10l4 4v10.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-2Z"}],["path",{d:"M10 2v4h6"}],["path",{d:"M18 18v-7h-8v7"}],["path",{d:"M18 22H4a2 2 0 0 1-2-2V6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tx=["svg",o,[["path",{d:"M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"}],["polyline",{points:"17 21 17 13 7 13 7 21"}],["polyline",{points:"7 3 7 8 15 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sa=["svg",o,[["circle",{cx:"19",cy:"19",r:"2"}],["circle",{cx:"5",cy:"5",r:"2"}],["path",{d:"M5 7v12h12"}],["path",{d:"m5 19 6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bx=["svg",o,[["path",{d:"m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"}],["path",{d:"m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"}],["path",{d:"M7 21h10"}],["path",{d:"M12 3v18"}],["path",{d:"M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ox=["svg",o,[["path",{d:"M21 3 9 15"}],["path",{d:"M12 3H3v18h18v-9"}],["path",{d:"M16 3h5v5"}],["path",{d:"M14 15H9v-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ex=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}],["path",{d:"M8 7v10"}],["path",{d:"M12 7v10"}],["path",{d:"M17 7v10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rx=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}],["circle",{cx:"12",cy:"12",r:"1"}],["path",{d:"M5 12s2.5-5 7-5 7 5 7 5-2.5 5-7 5-7-5-7-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zx=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}],["path",{d:"M8 14s1.5 2 4 2 4-2 4-2"}],["path",{d:"M9 9h.01"}],["path",{d:"M15 9h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ix=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}],["path",{d:"M7 12h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $x=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}],["circle",{cx:"12",cy:"12",r:"3"}],["path",{d:"m16 16-1.9-1.9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zx=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}],["path",{d:"M7 8h8"}],["path",{d:"M7 12h10"}],["path",{d:"M7 16h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wx=["svg",o,[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nx=["svg",o,[["circle",{cx:"7.5",cy:"7.5",r:".5"}],["circle",{cx:"18.5",cy:"5.5",r:".5"}],["circle",{cx:"11.5",cy:"11.5",r:".5"}],["circle",{cx:"7.5",cy:"16.5",r:".5"}],["circle",{cx:"17.5",cy:"14.5",r:".5"}],["path",{d:"M3 3v18h18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jx=["svg",o,[["circle",{cx:"12",cy:"10",r:"1"}],["path",{d:"M22 20V8h-4l-6-4-6 4H2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2Z"}],["path",{d:"M6 17v.01"}],["path",{d:"M6 13v.01"}],["path",{d:"M18 17v.01"}],["path",{d:"M18 13v.01"}],["path",{d:"M14 22v-5a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ux=["svg",o,[["path",{d:"m4 6 8-4 8 4"}],["path",{d:"m18 10 4 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8l4-2"}],["path",{d:"M14 22v-4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v4"}],["path",{d:"M18 5v17"}],["path",{d:"M6 5v17"}],["circle",{cx:"12",cy:"9",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qx=["svg",o,[["path",{d:"M5.42 9.42 8 12"}],["circle",{cx:"4",cy:"8",r:"2"}],["path",{d:"m14 6-8.58 8.58"}],["circle",{cx:"4",cy:"16",r:"2"}],["path",{d:"M10.8 14.8 14 18"}],["path",{d:"M16 12h-2"}],["path",{d:"M22 12h-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gx=["svg",o,[["path",{d:"M4 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2"}],["path",{d:"M10 22H8"}],["path",{d:"M16 22h-2"}],["circle",{cx:"8",cy:"8",r:"2"}],["path",{d:"M9.414 9.414 12 12"}],["path",{d:"M14.8 14.8 18 18"}],["circle",{cx:"8",cy:"16",r:"2"}],["path",{d:"m18 6-8.586 8.586"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xx=["svg",o,[["rect",{width:"20",height:"20",x:"2",y:"2",rx:"2"}],["circle",{cx:"8",cy:"8",r:"2"}],["path",{d:"M9.414 9.414 12 12"}],["path",{d:"M14.8 14.8 18 18"}],["circle",{cx:"8",cy:"16",r:"2"}],["path",{d:"m18 6-8.586 8.586"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yx=["svg",o,[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kx=["svg",o,[["path",{d:"M13 3H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-3"}],["path",{d:"M8 21h8"}],["path",{d:"M12 17v4"}],["path",{d:"m22 3-5 5"}],["path",{d:"m17 3 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jx=["svg",o,[["path",{d:"M13 3H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-3"}],["path",{d:"M8 21h8"}],["path",{d:"M12 17v4"}],["path",{d:"m17 8 5-5"}],["path",{d:"M17 3h5v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qx=["svg",o,[["path",{d:"M8 21h12a2 2 0 0 0 2-2v-2H10v2a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v3h4"}],["path",{d:"M19 17V5a2 2 0 0 0-2-2H4"}],["path",{d:"M15 8h-5"}],["path",{d:"M15 12h-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tm=["svg",o,[["path",{d:"M8 21h12a2 2 0 0 0 2-2v-2H10v2a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v3h4"}],["path",{d:"M19 17V5a2 2 0 0 0-2-2H4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const em=["svg",o,[["path",{d:"m8 11 2 2 4-4"}],["circle",{cx:"11",cy:"11",r:"8"}],["path",{d:"m21 21-4.3-4.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sm=["svg",o,[["path",{d:"m9 9-2 2 2 2"}],["path",{d:"m13 13 2-2-2-2"}],["circle",{cx:"11",cy:"11",r:"8"}],["path",{d:"m21 21-4.3-4.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const am=["svg",o,[["path",{d:"m13.5 8.5-5 5"}],["circle",{cx:"11",cy:"11",r:"8"}],["path",{d:"m21 21-4.3-4.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const im=["svg",o,[["path",{d:"m13.5 8.5-5 5"}],["path",{d:"m8.5 8.5 5 5"}],["circle",{cx:"11",cy:"11",r:"8"}],["path",{d:"m21 21-4.3-4.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nm=["svg",o,[["circle",{cx:"11",cy:"11",r:"8"}],["path",{d:"m21 21-4.3-4.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const aa=["svg",o,[["path",{d:"m3 3 3 9-3 9 19-9Z"}],["path",{d:"M6 12h16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const om=["svg",o,[["rect",{x:"14",y:"14",width:"8",height:"8",rx:"2"}],["rect",{x:"2",y:"2",width:"8",height:"8",rx:"2"}],["path",{d:"M7 14v1a2 2 0 0 0 2 2h1"}],["path",{d:"M14 7h1a2 2 0 0 1 2 2v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rm=["svg",o,[["path",{d:"m22 2-7 20-4-9-9-4Z"}],["path",{d:"M22 2 11 13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hm=["svg",o,[["line",{x1:"3",x2:"21",y1:"12",y2:"12"}],["polyline",{points:"8 8 12 4 16 8"}],["polyline",{points:"16 16 12 20 8 16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cm=["svg",o,[["line",{x1:"12",x2:"12",y1:"3",y2:"21"}],["polyline",{points:"8 8 4 12 8 16"}],["polyline",{points:"16 16 20 12 16 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lm=["svg",o,[["circle",{cx:"12",cy:"12",r:"3"}],["path",{d:"M4.5 10H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-.5"}],["path",{d:"M4.5 14H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2h-.5"}],["path",{d:"M6 6h.01"}],["path",{d:"M6 18h.01"}],["path",{d:"m15.7 13.4-.9-.3"}],["path",{d:"m9.2 10.9-.9-.3"}],["path",{d:"m10.6 15.7.3-.9"}],["path",{d:"m13.6 15.7-.4-1"}],["path",{d:"m10.8 9.3-.4-1"}],["path",{d:"m8.3 13.6 1-.4"}],["path",{d:"m14.7 10.8 1-.4"}],["path",{d:"m13.4 8.3-.3.9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dm=["svg",o,[["path",{d:"M6 10H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"}],["path",{d:"M6 14H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2h-2"}],["path",{d:"M6 6h.01"}],["path",{d:"M6 18h.01"}],["path",{d:"m13 6-4 6h6l-4 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pm=["svg",o,[["path",{d:"M7 2h13a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-5"}],["path",{d:"M10 10 2.5 2.5C2 2 2 2.5 2 5v3a2 2 0 0 0 2 2h6z"}],["path",{d:"M22 17v-1a2 2 0 0 0-2-2h-1"}],["path",{d:"M4 14a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16.5l1-.5.5.5-8-8H4z"}],["path",{d:"M6 18h.01"}],["path",{d:"m2 2 20 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gm=["svg",o,[["rect",{width:"20",height:"8",x:"2",y:"2",rx:"2",ry:"2"}],["rect",{width:"20",height:"8",x:"2",y:"14",rx:"2",ry:"2"}],["line",{x1:"6",x2:"6.01",y1:"6",y2:"6"}],["line",{x1:"6",x2:"6.01",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const um=["svg",o,[["path",{d:"M20 7h-9"}],["path",{d:"M14 17H5"}],["circle",{cx:"17",cy:"17",r:"3"}],["circle",{cx:"7",cy:"7",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fm=["svg",o,[["path",{d:"M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"}],["circle",{cx:"12",cy:"12",r:"3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vm=["svg",o,[["path",{d:"M8.3 10a.7.7 0 0 1-.626-1.079L11.4 3a.7.7 0 0 1 1.198-.043L16.3 8.9a.7.7 0 0 1-.572 1.1Z"}],["rect",{x:"3",y:"14",width:"7",height:"7",rx:"1"}],["circle",{cx:"17.5",cy:"17.5",r:"3.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xm=["svg",o,[["circle",{cx:"18",cy:"5",r:"3"}],["circle",{cx:"6",cy:"12",r:"3"}],["circle",{cx:"18",cy:"19",r:"3"}],["line",{x1:"8.59",x2:"15.42",y1:"13.51",y2:"17.49"}],["line",{x1:"15.41",x2:"8.59",y1:"6.51",y2:"10.49"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mm=["svg",o,[["path",{d:"M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"}],["polyline",{points:"16 6 12 2 8 6"}],["line",{x1:"12",x2:"12",y1:"2",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Mm=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["line",{x1:"3",x2:"21",y1:"9",y2:"9"}],["line",{x1:"3",x2:"21",y1:"15",y2:"15"}],["line",{x1:"9",x2:"9",y1:"9",y2:"21"}],["line",{x1:"15",x2:"15",y1:"9",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ym=["svg",o,[["path",{d:"M14 11a2 2 0 1 1-4 0 4 4 0 0 1 8 0 6 6 0 0 1-12 0 8 8 0 0 1 16 0 10 10 0 1 1-20 0 11.93 11.93 0 0 1 2.42-7.22 2 2 0 1 1 3.16 2.44"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bm=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"M12 8v4"}],["path",{d:"M12 16h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wm=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"m4 5 14 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _m=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"m9 12 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const km=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"M8 11h.01"}],["path",{d:"M12 11h.01"}],["path",{d:"M16 11h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cm=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"M12 22V2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sm=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"M8 11h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Lm=["svg",o,[["path",{d:"M19.7 14a6.9 6.9 0 0 0 .3-2V5l-8-3-3.2 1.2"}],["path",{d:"m2 2 20 20"}],["path",{d:"M4.7 4.7 4 5v7c0 6 8 10 8 10a20.3 20.3 0 0 0 5.62-4.38"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Am=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"M8 11h8"}],["path",{d:"M12 15V7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hm=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"M9.1 9a3 3 0 0 1 5.82 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ia=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}],["path",{d:"m14.5 9-5 5"}],["path",{d:"m9.5 9 5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vm=["svg",o,[["path",{d:"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pm=["svg",o,[["circle",{cx:"12",cy:"12",r:"8"}],["path",{d:"M12 2v7.5"}],["path",{d:"m19 5-5.23 5.23"}],["path",{d:"M22 12h-7.5"}],["path",{d:"m19 19-5.23-5.23"}],["path",{d:"M12 14.5V22"}],["path",{d:"M10.23 13.77 5 19"}],["path",{d:"M9.5 12H2"}],["path",{d:"M10.23 10.23 5 5"}],["circle",{cx:"12",cy:"12",r:"2.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dm=["svg",o,[["path",{d:"M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1 .6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76"}],["path",{d:"M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"}],["path",{d:"M12 10v4"}],["path",{d:"M12 2v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fm=["svg",o,[["path",{d:"M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Tm=["svg",o,[["path",{d:"M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"}],["path",{d:"M3 6h18"}],["path",{d:"M16 10a4 4 0 0 1-8 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bm=["svg",o,[["path",{d:"m5 11 4-7"}],["path",{d:"m19 11-4-7"}],["path",{d:"M2 11h20"}],["path",{d:"m3.5 11 1.6 7.4a2 2 0 0 0 2 1.6h9.8c.9 0 1.8-.7 2-1.6l1.7-7.4"}],["path",{d:"m9 11 1 9"}],["path",{d:"M4.5 15.5h15"}],["path",{d:"m15 11-1 9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Om=["svg",o,[["circle",{cx:"8",cy:"21",r:"1"}],["circle",{cx:"19",cy:"21",r:"1"}],["path",{d:"M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Em=["svg",o,[["path",{d:"M2 22v-5l5-5 5 5-5 5z"}],["path",{d:"M9.5 14.5 16 8"}],["path",{d:"m17 2 5 5-.5.5a3.53 3.53 0 0 1-5 0s0 0 0 0a3.53 3.53 0 0 1 0-5L17 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rm=["svg",o,[["path",{d:"m4 4 2.5 2.5"}],["path",{d:"M13.5 6.5a4.95 4.95 0 0 0-7 7"}],["path",{d:"M15 5 5 15"}],["path",{d:"M14 17v.01"}],["path",{d:"M10 16v.01"}],["path",{d:"M13 13v.01"}],["path",{d:"M16 10v.01"}],["path",{d:"M11 20v.01"}],["path",{d:"M17 14v.01"}],["path",{d:"M20 11v.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zm=["svg",o,[["path",{d:"m15 15 6 6m-6-6v4.8m0-4.8h4.8"}],["path",{d:"M9 19.8V15m0 0H4.2M9 15l-6 6"}],["path",{d:"M15 4.2V9m0 0h4.8M15 9l6-6"}],["path",{d:"M9 4.2V9m0 0H4.2M9 9 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Im=["svg",o,[["path",{d:"M12 22v-7l-2-2"}],["path",{d:"M17 8v.8A6 6 0 0 1 13.8 20v0H10v0A6.5 6.5 0 0 1 7 8h0a5 5 0 0 1 10 0Z"}],["path",{d:"m14 14-2 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $m=["svg",o,[["path",{d:"M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.7-1.1 2-1.7 3.3-1.7H22"}],["path",{d:"m18 2 4 4-4 4"}],["path",{d:"M2 6h1.9c1.5 0 2.9.9 3.6 2.2"}],["path",{d:"M22 18h-5.9c-1.3 0-2.6-.7-3.3-1.8l-.5-.8"}],["path",{d:"m18 14 4 4-4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zm=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M16 8.9V7H8l4 5-4 5h8v-1.9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wm=["svg",o,[["path",{d:"M18 7V4H6l6 8-6 8h12v-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Nm=["svg",o,[["path",{d:"M2 20h.01"}],["path",{d:"M7 20v-4"}],["path",{d:"M12 20v-8"}],["path",{d:"M17 20V8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jm=["svg",o,[["path",{d:"M2 20h.01"}],["path",{d:"M7 20v-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Um=["svg",o,[["path",{d:"M2 20h.01"}],["path",{d:"M7 20v-4"}],["path",{d:"M12 20v-8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qm=["svg",o,[["path",{d:"M2 20h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gm=["svg",o,[["path",{d:"M2 20h.01"}],["path",{d:"M7 20v-4"}],["path",{d:"M12 20v-8"}],["path",{d:"M17 20V8"}],["path",{d:"M22 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xm=["svg",o,[["path",{d:"M10 9H4L2 7l2-2h6"}],["path",{d:"M14 5h6l2 2-2 2h-6"}],["path",{d:"M10 22V4a2 2 0 1 1 4 0v18"}],["path",{d:"M8 22h8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ym=["svg",o,[["path",{d:"M12 3v3"}],["path",{d:"M18.5 13h-13L2 9.5 5.5 6h13L22 9.5Z"}],["path",{d:"M12 13v8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Km=["svg",o,[["path",{d:"M7 12a5 5 0 0 1 5-5v0a5 5 0 0 1 5 5v6H7v-6Z"}],["path",{d:"M5 20a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v2H5v-2Z"}],["path",{d:"M21 12h1"}],["path",{d:"M18.5 4.5 18 5"}],["path",{d:"M2 12h1"}],["path",{d:"M12 2v1"}],["path",{d:"m4.929 4.929.707.707"}],["path",{d:"M12 12v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jm=["svg",o,[["polygon",{points:"19 20 9 12 19 4 19 20"}],["line",{x1:"5",x2:"5",y1:"19",y2:"5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qm=["svg",o,[["polygon",{points:"5 4 15 12 5 20 5 4"}],["line",{x1:"19",x2:"19",y1:"5",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tM=["svg",o,[["circle",{cx:"9",cy:"12",r:"1"}],["circle",{cx:"15",cy:"12",r:"1"}],["path",{d:"M8 20v2h8v-2"}],["path",{d:"m12.5 17-.5-1-.5 1h1z"}],["path",{d:"M16 20a2 2 0 0 0 1.56-3.25 8 8 0 1 0-11.12 0A2 2 0 0 0 8 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const eM=["svg",o,[["rect",{width:"3",height:"8",x:"13",y:"2",rx:"1.5"}],["path",{d:"M19 8.5V10h1.5A1.5 1.5 0 1 0 19 8.5"}],["rect",{width:"3",height:"8",x:"8",y:"14",rx:"1.5"}],["path",{d:"M5 15.5V14H3.5A1.5 1.5 0 1 0 5 15.5"}],["rect",{width:"8",height:"3",x:"14",y:"13",rx:"1.5"}],["path",{d:"M15.5 19H14v1.5a1.5 1.5 0 1 0 1.5-1.5"}],["rect",{width:"8",height:"3",x:"2",y:"8",rx:"1.5"}],["path",{d:"M8.5 5H10V3.5A1.5 1.5 0 1 0 8.5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sM=["svg",o,[["path",{d:"M22 2 2 22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const aM=["svg",o,[["path",{d:"m8 14-6 6h9v-3"}],["path",{d:"M18.37 3.63 8 14l3 3L21.37 6.63a2.12 2.12 0 1 0-3-3Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const iM=["svg",o,[["line",{x1:"21",x2:"14",y1:"4",y2:"4"}],["line",{x1:"10",x2:"3",y1:"4",y2:"4"}],["line",{x1:"21",x2:"12",y1:"12",y2:"12"}],["line",{x1:"8",x2:"3",y1:"12",y2:"12"}],["line",{x1:"21",x2:"16",y1:"20",y2:"20"}],["line",{x1:"12",x2:"3",y1:"20",y2:"20"}],["line",{x1:"14",x2:"14",y1:"2",y2:"6"}],["line",{x1:"8",x2:"8",y1:"10",y2:"14"}],["line",{x1:"16",x2:"16",y1:"18",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nM=["svg",o,[["line",{x1:"4",x2:"4",y1:"21",y2:"14"}],["line",{x1:"4",x2:"4",y1:"10",y2:"3"}],["line",{x1:"12",x2:"12",y1:"21",y2:"12"}],["line",{x1:"12",x2:"12",y1:"8",y2:"3"}],["line",{x1:"20",x2:"20",y1:"21",y2:"16"}],["line",{x1:"20",x2:"20",y1:"12",y2:"3"}],["line",{x1:"2",x2:"6",y1:"14",y2:"14"}],["line",{x1:"10",x2:"14",y1:"8",y2:"8"}],["line",{x1:"18",x2:"22",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const oM=["svg",o,[["rect",{width:"14",height:"20",x:"5",y:"2",rx:"2",ry:"2"}],["path",{d:"M12.667 8 10 12h4l-2.667 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rM=["svg",o,[["rect",{width:"7",height:"12",x:"2",y:"6",rx:"1"}],["path",{d:"M13 8.32a7.43 7.43 0 0 1 0 7.36"}],["path",{d:"M16.46 6.21a11.76 11.76 0 0 1 0 11.58"}],["path",{d:"M19.91 4.1a15.91 15.91 0 0 1 .01 15.8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hM=["svg",o,[["rect",{width:"14",height:"20",x:"5",y:"2",rx:"2",ry:"2"}],["path",{d:"M12 18h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cM=["svg",o,[["path",{d:"M22 11v1a10 10 0 1 1-9-10"}],["path",{d:"M8 14s1.5 2 4 2 4-2 4-2"}],["line",{x1:"9",x2:"9.01",y1:"9",y2:"9"}],["line",{x1:"15",x2:"15.01",y1:"9",y2:"9"}],["path",{d:"M16 5h6"}],["path",{d:"M19 2v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const lM=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M8 14s1.5 2 4 2 4-2 4-2"}],["line",{x1:"9",x2:"9.01",y1:"9",y2:"9"}],["line",{x1:"15",x2:"15.01",y1:"9",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dM=["svg",o,[["path",{d:"M2 13a6 6 0 1 0 12 0 4 4 0 1 0-8 0 2 2 0 0 0 4 0"}],["circle",{cx:"10",cy:"13",r:"8"}],["path",{d:"M2 21h12c4.4 0 8-3.6 8-8V7a2 2 0 1 0-4 0v6"}],["path",{d:"M18 3 19.1 5.2"}],["path",{d:"M22 3 20.9 5.2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pM=["svg",o,[["line",{x1:"2",x2:"22",y1:"12",y2:"12"}],["line",{x1:"12",x2:"12",y1:"2",y2:"22"}],["path",{d:"m20 16-4-4 4-4"}],["path",{d:"m4 8 4 4-4 4"}],["path",{d:"m16 4-4 4-4-4"}],["path",{d:"m8 20 4-4 4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gM=["svg",o,[["path",{d:"M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3"}],["path",{d:"M2 11v5a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H6v-2a2 2 0 0 0-4 0Z"}],["path",{d:"M4 18v2"}],["path",{d:"M20 18v2"}],["path",{d:"M12 4v9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uM=["svg",o,[["path",{d:"M12 21a9 9 0 0 0 9-9H3a9 9 0 0 0 9 9Z"}],["path",{d:"M7 21h10"}],["path",{d:"M19.5 12 22 6"}],["path",{d:"M16.25 3c.27.1.8.53.75 1.36-.06.83-.93 1.2-1 2.02-.05.78.34 1.24.73 1.62"}],["path",{d:"M11.25 3c.27.1.8.53.74 1.36-.05.83-.93 1.2-.98 2.02-.06.78.33 1.24.72 1.62"}],["path",{d:"M6.25 3c.27.1.8.53.75 1.36-.06.83-.93 1.2-1 2.02-.05.78.34 1.24.74 1.62"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fM=["svg",o,[["path",{d:"M22 17v1c0 .5-.5 1-1 1H3c-.5 0-1-.5-1-1v-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vM=["svg",o,[["path",{d:"M5 9c-1.5 1.5-3 3.2-3 5.5A5.5 5.5 0 0 0 7.5 20c1.8 0 3-.5 4.5-2 1.5 1.5 2.7 2 4.5 2a5.5 5.5 0 0 0 5.5-5.5c0-2.3-1.5-4-3-5.5l-7-7-7 7Z"}],["path",{d:"M12 18v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xM=["svg",o,[["path",{d:"m12 3-1.9 5.8a2 2 0 0 1-1.287 1.288L3 12l5.8 1.9a2 2 0 0 1 1.288 1.287L12 21l1.9-5.8a2 2 0 0 1 1.287-1.288L21 12l-5.8-1.9a2 2 0 0 1-1.288-1.287Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const na=["svg",o,[["path",{d:"m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"}],["path",{d:"M5 3v4"}],["path",{d:"M19 17v4"}],["path",{d:"M3 5h4"}],["path",{d:"M17 19h4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const mM=["svg",o,[["rect",{width:"16",height:"20",x:"4",y:"2",rx:"2"}],["path",{d:"M12 6h.01"}],["circle",{cx:"12",cy:"14",r:"4"}],["path",{d:"M12 14h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const MM=["svg",o,[["path",{d:"M8.8 20v-4.1l1.9.2a2.3 2.3 0 0 0 2.164-2.1V8.3A5.37 5.37 0 0 0 2 8.25c0 2.8.656 3.054 1 4.55a5.77 5.77 0 0 1 .029 2.758L2 20"}],["path",{d:"M19.8 17.8a7.5 7.5 0 0 0 .003-10.603"}],["path",{d:"M17 15a3.5 3.5 0 0 0-.025-4.975"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yM=["svg",o,[["path",{d:"m6 16 6-12 6 12"}],["path",{d:"M8 12h8"}],["path",{d:"M4 21c1.1 0 1.1-1 2.3-1s1.1 1 2.3 1c1.1 0 1.1-1 2.3-1 1.1 0 1.1 1 2.3 1 1.1 0 1.1-1 2.3-1 1.1 0 1.1 1 2.3 1 1.1 0 1.1-1 2.3-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bM=["svg",o,[["path",{d:"m6 16 6-12 6 12"}],["path",{d:"M8 12h8"}],["path",{d:"m16 20 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wM=["svg",o,[["circle",{cx:"19",cy:"5",r:"2"}],["circle",{cx:"5",cy:"19",r:"2"}],["path",{d:"M5 17A12 12 0 0 1 17 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _M=["svg",o,[["path",{d:"M8 19H5c-1 0-2-1-2-2V7c0-1 1-2 2-2h3"}],["path",{d:"M16 5h3c1 0 2 1 2 2v10c0 1-1 2-2 2h-3"}],["line",{x1:"12",x2:"12",y1:"4",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const kM=["svg",o,[["path",{d:"M5 8V5c0-1 1-2 2-2h10c1 0 2 1 2 2v3"}],["path",{d:"M19 16v3c0 1-1 2-2 2H7c-1 0-2-1-2-2v-3"}],["line",{x1:"4",x2:"20",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const CM=["svg",o,[["path",{d:"M16 3h5v5"}],["path",{d:"M8 3H3v5"}],["path",{d:"M12 22v-8.3a4 4 0 0 0-1.172-2.872L3 3"}],["path",{d:"m15 9 6-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const SM=["svg",o,[["path",{d:"M3 3h.01"}],["path",{d:"M7 5h.01"}],["path",{d:"M11 7h.01"}],["path",{d:"M3 7h.01"}],["path",{d:"M7 9h.01"}],["path",{d:"M3 11h.01"}],["rect",{width:"4",height:"4",x:"15",y:"5"}],["path",{d:"m19 9 2 2v10c0 .6-.4 1-1 1h-6c-.6 0-1-.4-1-1V11l2-2"}],["path",{d:"m13 14 8-2"}],["path",{d:"m13 19 8-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const LM=["svg",o,[["path",{d:"M7 20h10"}],["path",{d:"M10 20c5.5-2.5.8-6.4 3-10"}],["path",{d:"M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"}],["path",{d:"M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const AM=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M12 8v8"}],["path",{d:"m8.5 14 7-4"}],["path",{d:"m8.5 10 7 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const HM=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"m10 10-2 2 2 2"}],["path",{d:"m14 14 2-2-2-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const VM=["svg",o,[["path",{d:"m10 10-2 2 2 2"}],["path",{d:"m14 14 2-2-2-2"}],["path",{d:"M5 21a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2"}],["path",{d:"M9 21h1"}],["path",{d:"M14 21h1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const PM=["svg",o,[["path",{d:"M5 21a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2"}],["path",{d:"M9 21h1"}],["path",{d:"M14 21h1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const DM=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["circle",{cx:"12",cy:"12",r:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const FM=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M7 10h10"}],["path",{d:"M7 14h10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const TM=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["line",{x1:"9",x2:"15",y1:"15",y2:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const BM=["svg",o,[["path",{d:"M4 10c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2"}],["path",{d:"M10 16c-1.1 0-2-.9-2-2v-4c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2"}],["rect",{width:"8",height:"8",x:"14",y:"14",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const oa=["svg",o,[["path",{d:"M18 21a6 6 0 0 0-12 0"}],["circle",{cx:"12",cy:"11",r:"4"}],["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ra=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["circle",{cx:"12",cy:"10",r:"3"}],["path",{d:"M7 21v-2a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const OM=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const EM=["svg",o,[["path",{d:"M18 6a4 4 0 0 0-4 4 7 7 0 0 0-7 7c0-5 4-5 4-10.5a4.5 4.5 0 1 0-9 0 2.5 2.5 0 0 0 5 0C7 10 3 11 3 17c0 2.8 2.2 5 5 5h10"}],["path",{d:"M16 20c0-1.7 1.3-3 3-3h1a2 2 0 0 0 2-2v-2a4 4 0 0 0-4-4V4"}],["path",{d:"M15.2 22a3 3 0 0 0-2.2-5"}],["path",{d:"M18 13h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const RM=["svg",o,[["path",{d:"M5 22h14"}],["path",{d:"M19.27 13.73A2.5 2.5 0 0 0 17.5 13h-11A2.5 2.5 0 0 0 4 15.5V17a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-1.5c0-.66-.26-1.3-.73-1.77Z"}],["path",{d:"M14 13V8.5C14 7 15 7 15 5a3 3 0 0 0-3-3c-1.66 0-3 1-3 3s1 2 1 3.5V13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zM=["svg",o,[["path",{d:"M12 17.8 5.8 21 7 14.1 2 9.3l7-1L12 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const IM=["svg",o,[["path",{d:"M8.34 8.34 2 9.27l5 4.87L5.82 21 12 17.77 18.18 21l-.59-3.43"}],["path",{d:"M18.42 12.76 22 9.27l-6.91-1L12 2l-1.44 2.91"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $M=["svg",o,[["polygon",{points:"12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ZM=["svg",o,[["line",{x1:"18",x2:"18",y1:"20",y2:"4"}],["polygon",{points:"14,20 4,12 14,4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const WM=["svg",o,[["line",{x1:"6",x2:"6",y1:"4",y2:"20"}],["polygon",{points:"10,4 20,12 10,20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const NM=["svg",o,[["path",{d:"M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"}],["path",{d:"M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"}],["circle",{cx:"20",cy:"10",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jM=["svg",o,[["path",{d:"M15.5 3H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h14a2 2 0 0 0 2-2V8.5L15.5 3Z"}],["path",{d:"M15 3v6h6"}],["path",{d:"M10 16s.8 1 2 1c1.3 0 2-1 2-1"}],["path",{d:"M8 13h0"}],["path",{d:"M16 13h0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const UM=["svg",o,[["path",{d:"M15.5 3H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h14a2 2 0 0 0 2-2V8.5L15.5 3Z"}],["path",{d:"M15 3v6h6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qM=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["rect",{width:"6",height:"6",x:"9",y:"9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const GM=["svg",o,[["path",{d:"m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"}],["path",{d:"M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"}],["path",{d:"M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"}],["path",{d:"M2 7h20"}],["path",{d:"M22 7v3a2 2 0 0 1-2 2v0a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 16 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 12 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 8 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 4 12v0a2 2 0 0 1-2-2V7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const XM=["svg",o,[["rect",{width:"20",height:"6",x:"2",y:"4",rx:"2"}],["rect",{width:"20",height:"6",x:"2",y:"14",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const YM=["svg",o,[["rect",{width:"6",height:"20",x:"4",y:"2",rx:"2"}],["rect",{width:"6",height:"20",x:"14",y:"2",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const KM=["svg",o,[["path",{d:"M16 4H9a3 3 0 0 0-2.83 4"}],["path",{d:"M14 12a4 4 0 0 1 0 8H6"}],["line",{x1:"4",x2:"20",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const JM=["svg",o,[["path",{d:"m4 5 8 8"}],["path",{d:"m12 5-8 8"}],["path",{d:"M20 19h-4c0-1.5.44-2 1.5-2.5S20 15.33 20 14c0-.47-.17-.93-.48-1.29a2.11 2.11 0 0 0-2.62-.44c-.42.24-.74.62-.9 1.07"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const QM=["svg",o,[["path",{d:"M7 13h4"}],["path",{d:"M15 13h2"}],["path",{d:"M7 9h2"}],["path",{d:"M13 9h4"}],["path",{d:"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t7=["svg",o,[["circle",{cx:"12",cy:"12",r:"4"}],["path",{d:"M12 4h.01"}],["path",{d:"M20 12h.01"}],["path",{d:"M12 20h.01"}],["path",{d:"M4 12h.01"}],["path",{d:"M17.657 6.343h.01"}],["path",{d:"M17.657 17.657h.01"}],["path",{d:"M6.343 17.657h.01"}],["path",{d:"M6.343 6.343h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e7=["svg",o,[["circle",{cx:"12",cy:"12",r:"4"}],["path",{d:"M12 3v1"}],["path",{d:"M12 20v1"}],["path",{d:"M3 12h1"}],["path",{d:"M20 12h1"}],["path",{d:"m18.364 5.636-.707.707"}],["path",{d:"m6.343 17.657-.707.707"}],["path",{d:"m5.636 5.636.707.707"}],["path",{d:"m17.657 17.657.707.707"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s7=["svg",o,[["path",{d:"M12 8a2.83 2.83 0 0 0 4 4 4 4 0 1 1-4-4"}],["path",{d:"M12 2v2"}],["path",{d:"M12 20v2"}],["path",{d:"m4.9 4.9 1.4 1.4"}],["path",{d:"m17.7 17.7 1.4 1.4"}],["path",{d:"M2 12h2"}],["path",{d:"M20 12h2"}],["path",{d:"m6.3 17.7-1.4 1.4"}],["path",{d:"m19.1 4.9-1.4 1.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a7=["svg",o,[["path",{d:"M10 9a3 3 0 1 0 0 6"}],["path",{d:"M2 12h1"}],["path",{d:"M14 21V3"}],["path",{d:"M10 4V3"}],["path",{d:"M10 21v-1"}],["path",{d:"m3.64 18.36.7-.7"}],["path",{d:"m4.34 6.34-.7-.7"}],["path",{d:"M14 12h8"}],["path",{d:"m17 4-3 3"}],["path",{d:"m14 17 3 3"}],["path",{d:"m21 15-3-3 3-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i7=["svg",o,[["circle",{cx:"12",cy:"12",r:"4"}],["path",{d:"M12 2v2"}],["path",{d:"M12 20v2"}],["path",{d:"m4.93 4.93 1.41 1.41"}],["path",{d:"m17.66 17.66 1.41 1.41"}],["path",{d:"M2 12h2"}],["path",{d:"M20 12h2"}],["path",{d:"m6.34 17.66-1.41 1.41"}],["path",{d:"m19.07 4.93-1.41 1.41"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n7=["svg",o,[["path",{d:"M12 2v8"}],["path",{d:"m4.93 10.93 1.41 1.41"}],["path",{d:"M2 18h2"}],["path",{d:"M20 18h2"}],["path",{d:"m19.07 10.93-1.41 1.41"}],["path",{d:"M22 22H2"}],["path",{d:"m8 6 4-4 4 4"}],["path",{d:"M16 18a4 4 0 0 0-8 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o7=["svg",o,[["path",{d:"M12 10V2"}],["path",{d:"m4.93 10.93 1.41 1.41"}],["path",{d:"M2 18h2"}],["path",{d:"M20 18h2"}],["path",{d:"m19.07 10.93-1.41 1.41"}],["path",{d:"M22 22H2"}],["path",{d:"m16 6-4 4-4-4"}],["path",{d:"M16 18a4 4 0 0 0-8 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r7=["svg",o,[["path",{d:"m4 19 8-8"}],["path",{d:"m12 19-8-8"}],["path",{d:"M20 12h-4c0-1.5.442-2 1.5-2.5S20 8.334 20 7.002c0-.472-.17-.93-.484-1.29a2.105 2.105 0 0 0-2.617-.436c-.42.239-.738.614-.899 1.06"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h7=["svg",o,[["path",{d:"M10 21V3h8"}],["path",{d:"M6 16h9"}],["path",{d:"M10 9.5h7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c7=["svg",o,[["path",{d:"M11 19H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5"}],["path",{d:"M13 5h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-5"}],["circle",{cx:"12",cy:"12",r:"3"}],["path",{d:"m18 22-3-3 3-3"}],["path",{d:"m6 2 3 3-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l7=["svg",o,[["polyline",{points:"14.5 17.5 3 6 3 3 6 3 17.5 14.5"}],["line",{x1:"13",x2:"19",y1:"19",y2:"13"}],["line",{x1:"16",x2:"20",y1:"16",y2:"20"}],["line",{x1:"19",x2:"21",y1:"21",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d7=["svg",o,[["polyline",{points:"14.5 17.5 3 6 3 3 6 3 17.5 14.5"}],["line",{x1:"13",x2:"19",y1:"19",y2:"13"}],["line",{x1:"16",x2:"20",y1:"16",y2:"20"}],["line",{x1:"19",x2:"21",y1:"21",y2:"19"}],["polyline",{points:"14.5 6.5 18 3 21 3 21 6 17.5 9.5"}],["line",{x1:"5",x2:"9",y1:"14",y2:"18"}],["line",{x1:"7",x2:"4",y1:"17",y2:"20"}],["line",{x1:"3",x2:"5",y1:"19",y2:"21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p7=["svg",o,[["path",{d:"m18 2 4 4"}],["path",{d:"m17 7 3-3"}],["path",{d:"M19 9 8.7 19.3c-1 1-2.5 1-3.4 0l-.6-.6c-1-1-1-2.5 0-3.4L15 5"}],["path",{d:"m9 11 4 4"}],["path",{d:"m5 19-3 3"}],["path",{d:"m14 4 6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g7=["svg",o,[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u7=["svg",o,[["path",{d:"M15 3v18"}],["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M21 9H3"}],["path",{d:"M21 15H3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f7=["svg",o,[["path",{d:"M12 3v18"}],["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M3 9h18"}],["path",{d:"M3 15h18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v7=["svg",o,[["rect",{width:"10",height:"14",x:"3",y:"8",rx:"2"}],["path",{d:"M5 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2h-2.4"}],["path",{d:"M8 18h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x7=["svg",o,[["rect",{width:"16",height:"20",x:"4",y:"2",rx:"2",ry:"2"}],["line",{x1:"12",x2:"12.01",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m7=["svg",o,[["circle",{cx:"7",cy:"7",r:"5"}],["circle",{cx:"17",cy:"17",r:"5"}],["path",{d:"M12 17h10"}],["path",{d:"m3.46 10.54 7.08-7.08"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M7=["svg",o,[["path",{d:"M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"}],["path",{d:"M7 7h.01"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y7=["svg",o,[["path",{d:"M9 5H2v7l6.29 6.29c.94.94 2.48.94 3.42 0l3.58-3.58c.94-.94.94-2.48 0-3.42L9 5Z"}],["path",{d:"M6 9.01V9"}],["path",{d:"m15 5 6.3 6.3a2.4 2.4 0 0 1 0 3.4L17 19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b7=["svg",o,[["path",{d:"M4 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w7=["svg",o,[["path",{d:"M4 4v16"}],["path",{d:"M9 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _7=["svg",o,[["path",{d:"M4 4v16"}],["path",{d:"M9 4v16"}],["path",{d:"M14 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k7=["svg",o,[["path",{d:"M4 4v16"}],["path",{d:"M9 4v16"}],["path",{d:"M14 4v16"}],["path",{d:"M19 4v16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C7=["svg",o,[["path",{d:"M4 4v16"}],["path",{d:"M9 4v16"}],["path",{d:"M14 4v16"}],["path",{d:"M19 4v16"}],["path",{d:"M22 6 2 18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S7=["svg",o,[["circle",{cx:"17",cy:"4",r:"2"}],["path",{d:"M15.59 5.41 5.41 15.59"}],["circle",{cx:"4",cy:"17",r:"2"}],["path",{d:"M12 22s-4-9-1.5-11.5S22 12 22 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L7=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["circle",{cx:"12",cy:"12",r:"6"}],["circle",{cx:"12",cy:"12",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A7=["svg",o,[["circle",{cx:"4",cy:"4",r:"2"}],["path",{d:"m14 5 3-3 3 3"}],["path",{d:"m14 10 3-3 3 3"}],["path",{d:"M17 14V2"}],["path",{d:"M17 14H7l-5 8h20Z"}],["path",{d:"M8 14v8"}],["path",{d:"m9 14 5 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H7=["svg",o,[["path",{d:"M3.5 21 14 3"}],["path",{d:"M20.5 21 10 3"}],["path",{d:"M15.5 21 12 15l-3.5 6"}],["path",{d:"M2 21h20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V7=["svg",o,[["path",{d:"m7 11 2-2-2-2"}],["path",{d:"M11 13h4"}],["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P7=["svg",o,[["polyline",{points:"4 17 10 11 4 5"}],["line",{x1:"12",x2:"20",y1:"19",y2:"19"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D7=["svg",o,[["path",{d:"M21 7 6.82 21.18a2.83 2.83 0 0 1-3.99-.01v0a2.83 2.83 0 0 1 0-4L17 3"}],["path",{d:"m16 2 6 6"}],["path",{d:"M12 16H4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F7=["svg",o,[["path",{d:"M14.5 2v17.5c0 1.4-1.1 2.5-2.5 2.5h0c-1.4 0-2.5-1.1-2.5-2.5V2"}],["path",{d:"M8.5 2h7"}],["path",{d:"M14.5 16h-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T7=["svg",o,[["path",{d:"M9 2v17.5A2.5 2.5 0 0 1 6.5 22v0A2.5 2.5 0 0 1 4 19.5V2"}],["path",{d:"M20 2v17.5a2.5 2.5 0 0 1-2.5 2.5v0a2.5 2.5 0 0 1-2.5-2.5V2"}],["path",{d:"M3 2h7"}],["path",{d:"M14 2h7"}],["path",{d:"M9 16H4"}],["path",{d:"M20 16h-5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B7=["svg",o,[["path",{d:"M5 4h1a3 3 0 0 1 3 3 3 3 0 0 1 3-3h1"}],["path",{d:"M13 20h-1a3 3 0 0 1-3-3 3 3 0 0 1-3 3H5"}],["path",{d:"M5 16H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h1"}],["path",{d:"M13 8h7a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-7"}],["path",{d:"M9 7v10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O7=["svg",o,[["path",{d:"M17 22h-1a4 4 0 0 1-4-4V6a4 4 0 0 1 4-4h1"}],["path",{d:"M7 22h1a4 4 0 0 0 4-4v-1"}],["path",{d:"M7 2h1a4 4 0 0 1 4 4v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E7=["svg",o,[["path",{d:"M17 6H3"}],["path",{d:"M21 12H8"}],["path",{d:"M21 18H8"}],["path",{d:"M3 12v6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ha=["svg",o,[["path",{d:"M5 3a2 2 0 0 0-2 2"}],["path",{d:"M19 3a2 2 0 0 1 2 2"}],["path",{d:"M21 19a2 2 0 0 1-2 2"}],["path",{d:"M5 21a2 2 0 0 1-2-2"}],["path",{d:"M9 3h1"}],["path",{d:"M9 21h1"}],["path",{d:"M14 3h1"}],["path",{d:"M14 21h1"}],["path",{d:"M3 9v1"}],["path",{d:"M21 9v1"}],["path",{d:"M3 14v1"}],["path",{d:"M21 14v1"}],["line",{x1:"7",x2:"15",y1:"8",y2:"8"}],["line",{x1:"7",x2:"17",y1:"12",y2:"12"}],["line",{x1:"7",x2:"13",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R7=["svg",o,[["path",{d:"M17 6.1H3"}],["path",{d:"M21 12.1H3"}],["path",{d:"M15.1 18H3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z7=["svg",o,[["path",{d:"M2 10s3-3 3-8"}],["path",{d:"M22 10s-3-3-3-8"}],["path",{d:"M10 2c0 4.4-3.6 8-8 8"}],["path",{d:"M14 2c0 4.4 3.6 8 8 8"}],["path",{d:"M2 10s2 2 2 5"}],["path",{d:"M22 10s-2 2-2 5"}],["path",{d:"M8 15h8"}],["path",{d:"M2 22v-1a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1"}],["path",{d:"M14 22v-1a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I7=["svg",o,[["path",{d:"M2 12h10"}],["path",{d:"M9 4v16"}],["path",{d:"m3 9 3 3-3 3"}],["path",{d:"M12 6 9 9 6 6"}],["path",{d:"m6 18 3-3 1.5 1.5"}],["path",{d:"M20 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $7=["svg",o,[["path",{d:"M12 9a4 4 0 0 0-2 7.5"}],["path",{d:"M12 3v2"}],["path",{d:"m6.6 18.4-1.4 1.4"}],["path",{d:"M20 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"}],["path",{d:"M4 13H2"}],["path",{d:"M6.34 7.34 4.93 5.93"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z7=["svg",o,[["path",{d:"M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W7=["svg",o,[["path",{d:"M17 14V2"}],["path",{d:"M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N7=["svg",o,[["path",{d:"M7 10v12"}],["path",{d:"M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j7=["svg",o,[["path",{d:"M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"}],["path",{d:"M13 5v2"}],["path",{d:"M13 17v2"}],["path",{d:"M13 11v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U7=["svg",o,[["path",{d:"M10 2h4"}],["path",{d:"M4.6 11a8 8 0 0 0 1.7 8.7 8 8 0 0 0 8.7 1.7"}],["path",{d:"M7.4 7.4a8 8 0 0 1 10.3 1 8 8 0 0 1 .9 10.2"}],["path",{d:"m2 2 20 20"}],["path",{d:"M12 12v-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q7=["svg",o,[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G7=["svg",o,[["line",{x1:"10",x2:"14",y1:"2",y2:"2"}],["line",{x1:"12",x2:"15",y1:"14",y2:"11"}],["circle",{cx:"12",cy:"14",r:"8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const X7=["svg",o,[["rect",{width:"20",height:"12",x:"2",y:"6",rx:"6",ry:"6"}],["circle",{cx:"8",cy:"12",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Y7=["svg",o,[["rect",{width:"20",height:"12",x:"2",y:"6",rx:"6",ry:"6"}],["circle",{cx:"16",cy:"12",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K7=["svg",o,[["path",{d:"M21 4H3"}],["path",{d:"M18 8H6"}],["path",{d:"M19 12H9"}],["path",{d:"M16 16h-6"}],["path",{d:"M11 20H9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const J7=["svg",o,[["ellipse",{cx:"12",cy:"11",rx:"3",ry:"2"}],["ellipse",{cx:"12",cy:"12.5",rx:"10",ry:"8.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Q7=["svg",o,[["path",{d:"M4 4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16"}],["path",{d:"M2 14h12"}],["path",{d:"M22 14h-2"}],["path",{d:"M12 20v-6"}],["path",{d:"m2 2 20 20"}],["path",{d:"M22 16V6a2 2 0 0 0-2-2H10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ty=["svg",o,[["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}],["path",{d:"M2 14h20"}],["path",{d:"M12 20v-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ey=["svg",o,[["path",{d:"M18.2 12.27 20 6H4l1.8 6.27a1 1 0 0 0 .95.73h10.5a1 1 0 0 0 .96-.73Z"}],["path",{d:"M8 13v9"}],["path",{d:"M16 22v-9"}],["path",{d:"m9 6 1 7"}],["path",{d:"m15 6-1 7"}],["path",{d:"M12 6V2"}],["path",{d:"M13 2h-2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sy=["svg",o,[["rect",{width:"18",height:"12",x:"3",y:"8",rx:"1"}],["path",{d:"M10 8V5c0-.6-.4-1-1-1H6a1 1 0 0 0-1 1v3"}],["path",{d:"M19 8V5c0-.6-.4-1-1-1h-3a1 1 0 0 0-1 1v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ay=["svg",o,[["path",{d:"M3 4h9l1 7"}],["path",{d:"M4 11V4"}],["path",{d:"M8 10V4"}],["path",{d:"M18 5c-.6 0-1 .4-1 1v5.6"}],["path",{d:"m10 11 11 .9c.6 0 .9.5.8 1.1l-.8 5h-1"}],["circle",{cx:"7",cy:"15",r:".5"}],["circle",{cx:"7",cy:"15",r:"5"}],["path",{d:"M16 18h-5"}],["circle",{cx:"18",cy:"18",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const iy=["svg",o,[["path",{d:"M9.3 6.2a4.55 4.55 0 0 0 5.4 0"}],["path",{d:"M7.9 10.7c.9.8 2.4 1.3 4.1 1.3s3.2-.5 4.1-1.3"}],["path",{d:"M13.9 3.5a1.93 1.93 0 0 0-3.8-.1l-3 10c-.1.2-.1.4-.1.6 0 1.7 2.2 3 5 3s5-1.3 5-3c0-.2 0-.4-.1-.5Z"}],["path",{d:"m7.5 12.2-4.7 2.7c-.5.3-.8.7-.8 1.1s.3.8.8 1.1l7.6 4.5c.9.5 2.1.5 3 0l7.6-4.5c.7-.3 1-.7 1-1.1s-.3-.8-.8-1.1l-4.7-2.8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ny=["svg",o,[["path",{d:"M2 22V12a10 10 0 1 1 20 0v10"}],["path",{d:"M15 6.8v1.4a3 2.8 0 1 1-6 0V6.8"}],["path",{d:"M10 15h.01"}],["path",{d:"M14 15h.01"}],["path",{d:"M10 19a4 4 0 0 1-4-4v-3a6 6 0 1 1 12 0v3a4 4 0 0 1-4 4Z"}],["path",{d:"m9 19-2 3"}],["path",{d:"m15 19 2 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const oy=["svg",o,[["path",{d:"M8 3.1V7a4 4 0 0 0 8 0V3.1"}],["path",{d:"m9 15-1-1"}],["path",{d:"m15 15 1-1"}],["path",{d:"M9 19c-2.8 0-5-2.2-5-5v-4a8 8 0 0 1 16 0v4c0 2.8-2.2 5-5 5Z"}],["path",{d:"m8 19-2 3"}],["path",{d:"m16 19 2 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ry=["svg",o,[["path",{d:"M2 17 17 2"}],["path",{d:"m2 14 8 8"}],["path",{d:"m5 11 8 8"}],["path",{d:"m8 8 8 8"}],["path",{d:"m11 5 8 8"}],["path",{d:"m14 2 8 8"}],["path",{d:"M7 22 22 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ca=["svg",o,[["rect",{width:"16",height:"16",x:"4",y:"3",rx:"2"}],["path",{d:"M4 11h16"}],["path",{d:"M12 3v8"}],["path",{d:"m8 19-2 3"}],["path",{d:"m18 22-2-3"}],["path",{d:"M8 15h0"}],["path",{d:"M16 15h0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const hy=["svg",o,[["path",{d:"M3 6h18"}],["path",{d:"M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"}],["path",{d:"M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"}],["line",{x1:"10",x2:"10",y1:"11",y2:"17"}],["line",{x1:"14",x2:"14",y1:"11",y2:"17"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const cy=["svg",o,[["path",{d:"M3 6h18"}],["path",{d:"M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"}],["path",{d:"M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ly=["svg",o,[["path",{d:"M8 19a4 4 0 0 1-2.24-7.32A3.5 3.5 0 0 1 9 6.03V6a3 3 0 1 1 6 0v.04a3.5 3.5 0 0 1 3.24 5.65A4 4 0 0 1 16 19Z"}],["path",{d:"M12 19v3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dy=["svg",o,[["path",{d:"m17 14 3 3.3a1 1 0 0 1-.7 1.7H4.7a1 1 0 0 1-.7-1.7L7 14h-.3a1 1 0 0 1-.7-1.7L9 9h-.2A1 1 0 0 1 8 7.3L12 3l4 4.3a1 1 0 0 1-.8 1.7H15l3 3.3a1 1 0 0 1-.7 1.7H17Z"}],["path",{d:"M12 22v-3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const py=["svg",o,[["path",{d:"M10 10v.2A3 3 0 0 1 8.9 16v0H5v0h0a3 3 0 0 1-1-5.8V10a3 3 0 0 1 6 0Z"}],["path",{d:"M7 16v6"}],["path",{d:"M13 19v3"}],["path",{d:"M12 19h8.3a1 1 0 0 0 .7-1.7L18 14h.3a1 1 0 0 0 .7-1.7L16 9h.2a1 1 0 0 0 .8-1.7L13 3l-1.4 1.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gy=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["rect",{width:"3",height:"9",x:"7",y:"7"}],["rect",{width:"3",height:"5",x:"14",y:"7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const uy=["svg",o,[["polyline",{points:"22 17 13.5 8.5 8.5 13.5 2 7"}],["polyline",{points:"16 17 22 17 22 11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fy=["svg",o,[["polyline",{points:"22 7 13.5 15.5 8.5 10.5 2 17"}],["polyline",{points:"16 7 22 7 22 13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const vy=["svg",o,[["path",{d:"M22 18a2 2 0 0 1-2 2H3c-1.1 0-1.3-.6-.4-1.3L20.4 4.3c.9-.7 1.6-.4 1.6.7Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xy=["svg",o,[["path",{d:"M13.73 4a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const my=["svg",o,[["path",{d:"M6 9H4.5a2.5 2.5 0 0 1 0-5H6"}],["path",{d:"M18 9h1.5a2.5 2.5 0 0 0 0-5H18"}],["path",{d:"M4 22h16"}],["path",{d:"M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"}],["path",{d:"M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"}],["path",{d:"M18 2H6v7a6 6 0 0 0 12 0V2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const My=["svg",o,[["path",{d:"M5 18H3c-.6 0-1-.4-1-1V7c0-.6.4-1 1-1h10c.6 0 1 .4 1 1v11"}],["path",{d:"M14 9h4l4 4v4c0 .6-.4 1-1 1h-2"}],["circle",{cx:"7",cy:"18",r:"2"}],["path",{d:"M15 18H9"}],["circle",{cx:"17",cy:"18",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const yy=["svg",o,[["path",{d:"m12 10 2 4v3a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-3a8 8 0 1 0-16 0v3a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-3l2-4h4Z"}],["path",{d:"M4.82 7.9 8 10"}],["path",{d:"M15.18 7.9 12 10"}],["path",{d:"M16.93 10H20a2 2 0 0 1 0 4H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const by=["svg",o,[["path",{d:"M7 21h10"}],["rect",{width:"20",height:"14",x:"2",y:"3",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const wy=["svg",o,[["rect",{width:"20",height:"15",x:"2",y:"7",rx:"2",ry:"2"}],["polyline",{points:"17 2 12 7 7 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _y=["svg",o,[["path",{d:"M21 2H3v16h5v4l4-4h5l4-4V2zm-10 9V7m5 4V7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ky=["svg",o,[["path",{d:"M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cy=["svg",o,[["polyline",{points:"4 7 4 4 20 4 20 7"}],["line",{x1:"9",x2:"15",y1:"20",y2:"20"}],["line",{x1:"12",x2:"12",y1:"4",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Sy=["svg",o,[["path",{d:"M12 2v1"}],["path",{d:"M15.5 21a1.85 1.85 0 0 1-3.5-1v-8H2a10 10 0 0 1 3.428-6.575"}],["path",{d:"M17.5 12H22A10 10 0 0 0 9.004 3.455"}],["path",{d:"m2 2 20 20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ly=["svg",o,[["path",{d:"M22 12a10.06 10.06 1 0 0-20 0Z"}],["path",{d:"M12 12v8a2 2 0 0 0 4 0"}],["path",{d:"M12 2v1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ay=["svg",o,[["path",{d:"M6 4v6a6 6 0 0 0 12 0V4"}],["line",{x1:"4",x2:"20",y1:"20",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hy=["svg",o,[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Vy=["svg",o,[["circle",{cx:"12",cy:"17",r:"1"}],["path",{d:"M3 7v6h6"}],["path",{d:"M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Py=["svg",o,[["path",{d:"M3 7v6h6"}],["path",{d:"M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Dy=["svg",o,[["path",{d:"M16 12h6"}],["path",{d:"M8 12H2"}],["path",{d:"M12 2v2"}],["path",{d:"M12 8v2"}],["path",{d:"M12 14v2"}],["path",{d:"M12 20v2"}],["path",{d:"m19 15 3-3-3-3"}],["path",{d:"m5 9-3 3 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fy=["svg",o,[["path",{d:"M12 22v-6"}],["path",{d:"M12 8V2"}],["path",{d:"M4 12H2"}],["path",{d:"M10 12H8"}],["path",{d:"M16 12h-2"}],["path",{d:"M22 12h-2"}],["path",{d:"m15 19-3 3-3-3"}],["path",{d:"m15 5-3-3-3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ty=["svg",o,[["rect",{width:"8",height:"6",x:"5",y:"4",rx:"1"}],["rect",{width:"8",height:"6",x:"11",y:"14",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const By=["svg",o,[["path",{d:"M15 7h2a5 5 0 0 1 0 10h-2m-6 0H7A5 5 0 0 1 7 7h2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Oy=["svg",o,[["path",{d:"m18.84 12.25 1.72-1.71h-.02a5.004 5.004 0 0 0-.12-7.07 5.006 5.006 0 0 0-6.95 0l-1.72 1.71"}],["path",{d:"m5.17 11.75-1.71 1.71a5.004 5.004 0 0 0 .12 7.07 5.006 5.006 0 0 0 6.95 0l1.71-1.71"}],["line",{x1:"8",x2:"8",y1:"2",y2:"5"}],["line",{x1:"2",x2:"5",y1:"8",y2:"8"}],["line",{x1:"16",x2:"16",y1:"19",y2:"22"}],["line",{x1:"19",x2:"22",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ey=["svg",o,[["circle",{cx:"12",cy:"16",r:"1"}],["rect",{x:"3",y:"10",width:"18",height:"12",rx:"2"}],["path",{d:"M7 10V7a5 5 0 0 1 9.33-2.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ry=["svg",o,[["rect",{width:"18",height:"11",x:"3",y:"11",rx:"2",ry:"2"}],["path",{d:"M7 11V7a5 5 0 0 1 9.9-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zy=["svg",o,[["path",{d:"m19 5 3-3"}],["path",{d:"m2 22 3-3"}],["path",{d:"M6.3 20.3a2.4 2.4 0 0 0 3.4 0L12 18l-6-6-2.3 2.3a2.4 2.4 0 0 0 0 3.4Z"}],["path",{d:"M7.5 13.5 10 11"}],["path",{d:"M10.5 16.5 13 14"}],["path",{d:"m12 6 6 6 2.3-2.3a2.4 2.4 0 0 0 0-3.4l-2.6-2.6a2.4 2.4 0 0 0-3.4 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Iy=["svg",o,[["path",{d:"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{d:"M12 12v9"}],["path",{d:"m16 16-4-4-4 4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $y=["svg",o,[["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["polyline",{points:"17 8 12 3 7 8"}],["line",{x1:"12",x2:"12",y1:"3",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zy=["svg",o,[["circle",{cx:"10",cy:"7",r:"1"}],["circle",{cx:"4",cy:"20",r:"1"}],["path",{d:"M4.7 19.3 19 5"}],["path",{d:"m21 3-3 1 2 2Z"}],["path",{d:"M9.26 7.68 5 12l2 5"}],["path",{d:"m10 14 5 2 3.5-3.5"}],["path",{d:"m18 12 1-1 1 1-1 1Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Wy=["svg",o,[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["circle",{cx:"9",cy:"7",r:"4"}],["polyline",{points:"16 11 18 13 22 9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ny=["svg",o,[["circle",{cx:"18",cy:"15",r:"3"}],["circle",{cx:"9",cy:"7",r:"4"}],["path",{d:"M10 15H6a4 4 0 0 0-4 4v2"}],["path",{d:"m21.7 16.4-.9-.3"}],["path",{d:"m15.2 13.9-.9-.3"}],["path",{d:"m16.6 18.7.3-.9"}],["path",{d:"m19.1 12.2.3-.9"}],["path",{d:"m19.6 18.7-.4-1"}],["path",{d:"m16.8 12.3-.4-1"}],["path",{d:"m14.3 16.6 1-.4"}],["path",{d:"m20.7 13.8 1-.4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const jy=["svg",o,[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["circle",{cx:"9",cy:"7",r:"4"}],["line",{x1:"22",x2:"16",y1:"11",y2:"11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Uy=["svg",o,[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["circle",{cx:"9",cy:"7",r:"4"}],["line",{x1:"19",x2:"19",y1:"8",y2:"14"}],["line",{x1:"22",x2:"16",y1:"11",y2:"11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const la=["svg",o,[["path",{d:"M2 21a8 8 0 0 1 13.292-6"}],["circle",{cx:"10",cy:"8",r:"5"}],["path",{d:"m16 19 2 2 4-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const da=["svg",o,[["path",{d:"M2 21a8 8 0 0 1 10.434-7.62"}],["circle",{cx:"10",cy:"8",r:"5"}],["circle",{cx:"18",cy:"18",r:"3"}],["path",{d:"m19.5 14.3-.4.9"}],["path",{d:"m16.9 20.8-.4.9"}],["path",{d:"m21.7 19.5-.9-.4"}],["path",{d:"m15.2 16.9-.9-.4"}],["path",{d:"m21.7 16.5-.9.4"}],["path",{d:"m15.2 19.1-.9.4"}],["path",{d:"m19.5 21.7-.4-.9"}],["path",{d:"m16.9 15.2-.4-.9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pa=["svg",o,[["path",{d:"M2 21a8 8 0 0 1 13.292-6"}],["circle",{cx:"10",cy:"8",r:"5"}],["path",{d:"M22 19h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ga=["svg",o,[["path",{d:"M2 21a8 8 0 0 1 13.292-6"}],["circle",{cx:"10",cy:"8",r:"5"}],["path",{d:"M19 16v6"}],["path",{d:"M22 19h-6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ua=["svg",o,[["path",{d:"M2 21a8 8 0 0 1 11.873-7"}],["circle",{cx:"10",cy:"8",r:"5"}],["path",{d:"m17 17 5 5"}],["path",{d:"m22 17-5 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fa=["svg",o,[["circle",{cx:"12",cy:"8",r:"5"}],["path",{d:"M20 21a8 8 0 0 0-16 0"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qy=["svg",o,[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["circle",{cx:"9",cy:"7",r:"4"}],["line",{x1:"17",x2:"22",y1:"8",y2:"13"}],["line",{x1:"22",x2:"17",y1:"8",y2:"13"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gy=["svg",o,[["path",{d:"M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"}],["circle",{cx:"12",cy:"7",r:"4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const va=["svg",o,[["path",{d:"M18 21a8 8 0 0 0-16 0"}],["circle",{cx:"10",cy:"8",r:"5"}],["path",{d:"M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xy=["svg",o,[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["circle",{cx:"9",cy:"7",r:"4"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Yy=["svg",o,[["path",{d:"m16 2-2.3 2.3a3 3 0 0 0 0 4.2l1.8 1.8a3 3 0 0 0 4.2 0L22 8"}],["path",{d:"M15 15 3.3 3.3a4.2 4.2 0 0 0 0 6l7.3 7.3c.7.7 2 .7 2.8 0L15 15Zm0 0 7 7"}],["path",{d:"m2.1 21.8 6.4-6.3"}],["path",{d:"m19 5-7 7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ky=["svg",o,[["path",{d:"M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"}],["path",{d:"M7 2v20"}],["path",{d:"M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Jy=["svg",o,[["path",{d:"M12 2v20"}],["path",{d:"M2 5h20"}],["path",{d:"M3 3v2"}],["path",{d:"M7 3v2"}],["path",{d:"M17 3v2"}],["path",{d:"M21 3v2"}],["path",{d:"m19 5-7 7-7-7"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qy=["svg",o,[["path",{d:"M8 21s-4-3-4-9 4-9 4-9"}],["path",{d:"M16 3s4 3 4 9-4 9-4 9"}],["line",{x1:"15",x2:"9",y1:"9",y2:"15"}],["line",{x1:"9",x2:"15",y1:"9",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const t9=["svg",o,[["path",{d:"M2 2a26.6 26.6 0 0 1 10 20c.9-6.82 1.5-9.5 4-14"}],["path",{d:"M16 8c4 0 6-2 6-6-4 0-6 2-6 6"}],["path",{d:"M17.41 3.6a10 10 0 1 0 3 3"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const e9=["svg",o,[["path",{d:"M2 12a5 5 0 0 0 5 5 8 8 0 0 1 5 2 8 8 0 0 1 5-2 5 5 0 0 0 5-5V7h-5a8 8 0 0 0-5 2 8 8 0 0 0-5-2H2Z"}],["path",{d:"M6 11c1.5 0 3 .5 3 2-2 0-3 0-3-2Z"}],["path",{d:"M18 11c-1.5 0-3 .5-3 2 2 0 3 0 3-2Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const s9=["svg",o,[["path",{d:"m2 8 2 2-2 2 2 2-2 2"}],["path",{d:"m22 8-2 2 2 2-2 2 2 2"}],["path",{d:"M8 8v10c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2"}],["path",{d:"M16 10.34V6c0-.55-.45-1-1-1h-4.34"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const a9=["svg",o,[["path",{d:"m2 8 2 2-2 2 2 2-2 2"}],["path",{d:"m22 8-2 2 2 2-2 2 2 2"}],["rect",{width:"8",height:"14",x:"8",y:"5",rx:"1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i9=["svg",o,[["path",{d:"M10.66 6H14a2 2 0 0 1 2 2v2.34l1 1L22 8v8"}],["path",{d:"M16 16a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h2l10 10Z"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const n9=["svg",o,[["path",{d:"m22 8-6 4 6 4V8Z"}],["rect",{width:"14",height:"12",x:"2",y:"6",rx:"2",ry:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const o9=["svg",o,[["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}],["path",{d:"M2 8h20"}],["circle",{cx:"8",cy:"14",r:"2"}],["path",{d:"M8 12h8"}],["circle",{cx:"16",cy:"14",r:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r9=["svg",o,[["path",{d:"M5 12s2.545-5 7-5c4.454 0 7 5 7 5s-2.546 5-7 5c-4.455 0-7-5-7-5z"}],["path",{d:"M12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2"}],["path",{d:"M21 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h9=["svg",o,[["circle",{cx:"6",cy:"12",r:"4"}],["circle",{cx:"18",cy:"12",r:"4"}],["line",{x1:"6",x2:"18",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c9=["svg",o,[["polygon",{points:"11 5 6 9 2 9 2 15 6 15 11 19 11 5"}],["path",{d:"M15.54 8.46a5 5 0 0 1 0 7.07"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l9=["svg",o,[["polygon",{points:"11 5 6 9 2 9 2 15 6 15 11 19 11 5"}],["path",{d:"M15.54 8.46a5 5 0 0 1 0 7.07"}],["path",{d:"M19.07 4.93a10 10 0 0 1 0 14.14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d9=["svg",o,[["polygon",{points:"11 5 6 9 2 9 2 15 6 15 11 19 11 5"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p9=["svg",o,[["polygon",{points:"11 5 6 9 2 9 2 15 6 15 11 19 11 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g9=["svg",o,[["path",{d:"m9 12 2 2 4-4"}],["path",{d:"M5 7c0-1.1.9-2 2-2h10a2 2 0 0 1 2 2v12H5V7Z"}],["path",{d:"M22 19H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u9=["svg",o,[["path",{d:"M17 14h.01"}],["path",{d:"M7 7h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f9=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M3 9a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2"}],["path",{d:"M3 11h3c.8 0 1.6.3 2.1.9l1.1.9c1.6 1.6 4.1 1.6 5.7 0l1.1-.9c.5-.5 1.3-.9 2.1-.9H21"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v9=["svg",o,[["path",{d:"M21 12V7H5a2 2 0 0 1 0-4h14v4"}],["path",{d:"M3 5v14a2 2 0 0 0 2 2h16v-5"}],["path",{d:"M18 12a2 2 0 0 0 0 4h4v-4Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x9=["svg",o,[["circle",{cx:"8",cy:"9",r:"2"}],["path",{d:"m9 17 6.1-6.1a2 2 0 0 1 2.81.01L22 15V5a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2"}],["path",{d:"M8 21h8"}],["path",{d:"M12 17v4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m9=["svg",o,[["path",{d:"m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72Z"}],["path",{d:"m14 7 3 3"}],["path",{d:"M5 6v4"}],["path",{d:"M19 14v4"}],["path",{d:"M10 2v2"}],["path",{d:"M7 8H3"}],["path",{d:"M21 16h-4"}],["path",{d:"M11 3H9"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M9=["svg",o,[["path",{d:"M15 4V2"}],["path",{d:"M15 16v-2"}],["path",{d:"M8 9h2"}],["path",{d:"M20 9h2"}],["path",{d:"M17.8 11.8 19 13"}],["path",{d:"M15 9h0"}],["path",{d:"M17.8 6.2 19 5"}],["path",{d:"m3 21 9-9"}],["path",{d:"M12.2 6.2 11 5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y9=["svg",o,[["path",{d:"M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3.26 6.5l8-3.2a2 2 0 0 1 1.48 0l8 3.2A2 2 0 0 1 22 8.35Z"}],["path",{d:"M6 18h12"}],["path",{d:"M6 14h12"}],["rect",{width:"12",height:"12",x:"6",y:"10"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b9=["svg",o,[["circle",{cx:"12",cy:"12",r:"6"}],["polyline",{points:"12 10 12 12 13 13"}],["path",{d:"m16.13 7.66-.81-4.05a2 2 0 0 0-2-1.61h-2.68a2 2 0 0 0-2 1.61l-.78 4.05"}],["path",{d:"m7.88 16.36.8 4a2 2 0 0 0 2 1.61h2.72a2 2 0 0 0 2-1.61l.81-4.05"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w9=["svg",o,[["path",{d:"M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _9=["svg",o,[["circle",{cx:"12",cy:"4.5",r:"2.5"}],["path",{d:"m10.2 6.3-3.9 3.9"}],["circle",{cx:"4.5",cy:"12",r:"2.5"}],["path",{d:"M7 12h10"}],["circle",{cx:"19.5",cy:"12",r:"2.5"}],["path",{d:"m13.8 17.7 3.9-3.9"}],["circle",{cx:"12",cy:"19.5",r:"2.5"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k9=["svg",o,[["circle",{cx:"12",cy:"10",r:"8"}],["circle",{cx:"12",cy:"10",r:"3"}],["path",{d:"M7 22h10"}],["path",{d:"M12 22v-4"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C9=["svg",o,[["path",{d:"M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 0 1 2 17c.01-.7.2-1.4.57-2"}],["path",{d:"m6 17 3.13-5.78c.53-.97.1-2.18-.5-3.1a4 4 0 1 1 6.89-4.06"}],["path",{d:"m12 6 3.13 5.73C15.66 12.7 16.9 13 18 13a4 4 0 0 1 0 8"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const S9=["svg",o,[["circle",{cx:"12",cy:"5",r:"3"}],["path",{d:"M6.5 8a2 2 0 0 0-1.905 1.46L2.1 18.5A2 2 0 0 0 4 21h16a2 2 0 0 0 1.925-2.54L19.4 9.5A2 2 0 0 0 17.48 8Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L9=["svg",o,[["path",{d:"m2 22 10-10"}],["path",{d:"m16 8-1.17 1.17"}],["path",{d:"M3.47 12.53 5 11l1.53 1.53a3.5 3.5 0 0 1 0 4.94L5 19l-1.53-1.53a3.5 3.5 0 0 1 0-4.94Z"}],["path",{d:"m8 8-.53.53a3.5 3.5 0 0 0 0 4.94L9 15l1.53-1.53c.55-.55.88-1.25.98-1.97"}],["path",{d:"M10.91 5.26c.15-.26.34-.51.56-.73L13 3l1.53 1.53a3.5 3.5 0 0 1 .28 4.62"}],["path",{d:"M20 2h2v2a4 4 0 0 1-4 4h-2V6a4 4 0 0 1 4-4Z"}],["path",{d:"M11.47 17.47 13 19l-1.53 1.53a3.5 3.5 0 0 1-4.94 0L5 19l1.53-1.53a3.5 3.5 0 0 1 4.94 0Z"}],["path",{d:"m16 16-.53.53a3.5 3.5 0 0 1-4.94 0L9 15l1.53-1.53a3.49 3.49 0 0 1 1.97-.98"}],["path",{d:"M18.74 13.09c.26-.15.51-.34.73-.56L21 11l-1.53-1.53a3.5 3.5 0 0 0-4.62-.28"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A9=["svg",o,[["path",{d:"M2 22 16 8"}],["path",{d:"M3.47 12.53 5 11l1.53 1.53a3.5 3.5 0 0 1 0 4.94L5 19l-1.53-1.53a3.5 3.5 0 0 1 0-4.94Z"}],["path",{d:"M7.47 8.53 9 7l1.53 1.53a3.5 3.5 0 0 1 0 4.94L9 15l-1.53-1.53a3.5 3.5 0 0 1 0-4.94Z"}],["path",{d:"M11.47 4.53 13 3l1.53 1.53a3.5 3.5 0 0 1 0 4.94L13 11l-1.53-1.53a3.5 3.5 0 0 1 0-4.94Z"}],["path",{d:"M20 2h2v2a4 4 0 0 1-4 4h-2V6a4 4 0 0 1 4-4Z"}],["path",{d:"M11.47 17.47 13 19l-1.53 1.53a3.5 3.5 0 0 1-4.94 0L5 19l1.53-1.53a3.5 3.5 0 0 1 4.94 0Z"}],["path",{d:"M15.47 13.47 17 15l-1.53 1.53a3.5 3.5 0 0 1-4.94 0L9 15l1.53-1.53a3.5 3.5 0 0 1 4.94 0Z"}],["path",{d:"M19.47 9.47 21 11l-1.53 1.53a3.5 3.5 0 0 1-4.94 0L13 11l1.53-1.53a3.5 3.5 0 0 1 4.94 0Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H9=["svg",o,[["circle",{cx:"7",cy:"12",r:"3"}],["path",{d:"M10 9v6"}],["circle",{cx:"17",cy:"12",r:"3"}],["path",{d:"M14 7v8"}],["path",{d:"M22 17v1c0 .5-.5 1-1 1H3c-.5 0-1-.5-1-1v-1"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V9=["svg",o,[["line",{x1:"2",x2:"22",y1:"2",y2:"22"}],["path",{d:"M8.5 16.5a5 5 0 0 1 7 0"}],["path",{d:"M2 8.82a15 15 0 0 1 4.17-2.65"}],["path",{d:"M10.66 5c4.01-.36 8.14.9 11.34 3.76"}],["path",{d:"M16.85 11.25a10 10 0 0 1 2.22 1.68"}],["path",{d:"M5 13a10 10 0 0 1 5.24-2.76"}],["line",{x1:"12",x2:"12.01",y1:"20",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P9=["svg",o,[["path",{d:"M5 13a10 10 0 0 1 14 0"}],["path",{d:"M8.5 16.5a5 5 0 0 1 7 0"}],["path",{d:"M2 8.82a15 15 0 0 1 20 0"}],["line",{x1:"12",x2:"12.01",y1:"20",y2:"20"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D9=["svg",o,[["path",{d:"M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"}],["path",{d:"M9.6 4.6A2 2 0 1 1 11 8H2"}],["path",{d:"M12.6 19.4A2 2 0 1 0 14 16H2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F9=["svg",o,[["path",{d:"M8 22h8"}],["path",{d:"M7 10h3m7 0h-1.343"}],["path",{d:"M12 15v7"}],["path",{d:"M7.307 7.307A12.33 12.33 0 0 0 7 10a5 5 0 0 0 7.391 4.391M8.638 2.981C8.75 2.668 8.872 2.34 9 2h6c1.5 4 2 6 2 8 0 .407-.05.809-.145 1.198"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const T9=["svg",o,[["path",{d:"M8 22h8"}],["path",{d:"M7 10h10"}],["path",{d:"M12 15v7"}],["path",{d:"M12 15a5 5 0 0 0 5-5c0-2-.5-4-2-8H9c-1.5 4-2 6-2 8a5 5 0 0 0 5 5Z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const B9=["svg",o,[["rect",{width:"8",height:"8",x:"3",y:"3",rx:"2"}],["path",{d:"M7 11v4a2 2 0 0 0 2 2h4"}],["rect",{width:"8",height:"8",x:"13",y:"13",rx:"2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O9=["svg",o,[["line",{x1:"3",x2:"21",y1:"6",y2:"6"}],["path",{d:"M3 12h15a3 3 0 1 1 0 6h-4"}],["polyline",{points:"16 16 14 18 16 20"}],["line",{x1:"3",x2:"10",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E9=["svg",o,[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const R9=["svg",o,[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m15 9-6 6"}],["path",{d:"m9 9 6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const z9=["svg",o,[["polygon",{points:"7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"}],["path",{d:"m15 9-6 6"}],["path",{d:"m9 9 6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I9=["svg",o,[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",ry:"2"}],["path",{d:"m15 9-6 6"}],["path",{d:"m9 9 6 6"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $9=["svg",o,[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Z9=["svg",o,[["path",{d:"M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"}],["path",{d:"m10 15 5-3-5-3z"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const W9=["svg",o,[["polyline",{points:"12.41 6.75 13 2 10.57 4.92"}],["polyline",{points:"18.57 12.91 21 10 15.66 10"}],["polyline",{points:"8 8 3 14 12 14 11 22 16 16"}],["line",{x1:"2",x2:"22",y1:"2",y2:"22"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const N9=["svg",o,[["polygon",{points:"13 2 3 14 12 14 11 22 21 10 12 10 13 2"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j9=["svg",o,[["circle",{cx:"11",cy:"11",r:"8"}],["line",{x1:"21",x2:"16.65",y1:"21",y2:"16.65"}],["line",{x1:"11",x2:"11",y1:"8",y2:"14"}],["line",{x1:"8",x2:"14",y1:"11",y2:"11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U9=["svg",o,[["circle",{cx:"11",cy:"11",r:"8"}],["line",{x1:"21",x2:"16.65",y1:"21",y2:"16.65"}],["line",{x1:"8",x2:"14",y1:"11",y2:"11"}]]];/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q9=Object.freeze(Object.defineProperty({__proto__:null,Accessibility:ln,Activity:pn,ActivitySquare:dn,AirVent:gn,Airplay:un,AlarmCheck:Ss,AlarmClock:vn,AlarmClockCheck:Ss,AlarmClockOff:fn,AlarmMinus:xn,AlarmPlus:mn,Album:Mn,AlertCircle:yn,AlertOctagon:bn,AlertTriangle:wn,AlignCenter:Cn,AlignCenterHorizontal:_n,AlignCenterVertical:kn,AlignEndHorizontal:Sn,AlignEndVertical:Ln,AlignHorizontalDistributeCenter:An,AlignHorizontalDistributeEnd:Hn,AlignHorizontalDistributeStart:Vn,AlignHorizontalJustifyCenter:Pn,AlignHorizontalJustifyEnd:Dn,AlignHorizontalJustifyStart:Fn,AlignHorizontalSpaceAround:Tn,AlignHorizontalSpaceBetween:Bn,AlignJustify:On,AlignLeft:En,AlignRight:Rn,AlignStartHorizontal:zn,AlignStartVertical:In,AlignVerticalDistributeCenter:$n,AlignVerticalDistributeEnd:Zn,AlignVerticalDistributeStart:Wn,AlignVerticalJustifyCenter:Nn,AlignVerticalJustifyEnd:jn,AlignVerticalJustifyStart:Un,AlignVerticalSpaceAround:qn,AlignVerticalSpaceBetween:Gn,Ampersand:Xn,Ampersands:Yn,Anchor:Kn,Angry:Jn,Annoyed:Qn,Antenna:to,Aperture:eo,AppWindow:so,Apple:ao,Archive:oo,ArchiveRestore:io,ArchiveX:no,AreaChart:ro,Armchair:ho,ArrowBigDown:lo,ArrowBigDownDash:co,ArrowBigLeft:go,ArrowBigLeftDash:po,ArrowBigRight:fo,ArrowBigRightDash:uo,ArrowBigUp:xo,ArrowBigUpDash:vo,ArrowDown:Fo,ArrowDown01:mo,ArrowDown10:Mo,ArrowDownAZ:Ls,ArrowDownAz:Ls,ArrowDownCircle:yo,ArrowDownFromLine:bo,ArrowDownLeft:ko,ArrowDownLeftFromCircle:wo,ArrowDownLeftSquare:_o,ArrowDownNarrowWide:Co,ArrowDownRight:Ao,ArrowDownRightFromCircle:So,ArrowDownRightSquare:Lo,ArrowDownSquare:Ho,ArrowDownToDot:Vo,ArrowDownToLine:Po,ArrowDownUp:Do,ArrowDownWideNarrow:As,ArrowDownZA:Hs,ArrowDownZa:Hs,ArrowLeft:zo,ArrowLeftCircle:To,ArrowLeftFromLine:Bo,ArrowLeftRight:Oo,ArrowLeftSquare:Eo,ArrowLeftToLine:Ro,ArrowRight:jo,ArrowRightCircle:Io,ArrowRightFromLine:$o,ArrowRightLeft:Zo,ArrowRightSquare:Wo,ArrowRightToLine:No,ArrowUp:rr,ArrowUp01:Uo,ArrowUp10:qo,ArrowUpAZ:Vs,ArrowUpAz:Vs,ArrowUpCircle:Go,ArrowUpDown:Xo,ArrowUpFromDot:Yo,ArrowUpFromLine:Ko,ArrowUpLeft:tr,ArrowUpLeftFromCircle:Jo,ArrowUpLeftSquare:Qo,ArrowUpNarrowWide:Ps,ArrowUpRight:ar,ArrowUpRightFromCircle:er,ArrowUpRightSquare:sr,ArrowUpSquare:ir,ArrowUpToLine:nr,ArrowUpWideNarrow:or,ArrowUpZA:Ds,ArrowUpZa:Ds,ArrowsUpFromLine:hr,Asterisk:cr,AtSign:lr,Atom:dr,AudioLines:pr,AudioWaveform:gr,Award:ur,Axe:fr,Axis3D:Fs,Axis3d:Fs,Baby:vr,Backpack:xr,Badge:Fr,BadgeAlert:mr,BadgeCent:Mr,BadgeCheck:Ts,BadgeDollarSign:yr,BadgeEuro:br,BadgeHelp:wr,BadgeIndianRupee:_r,BadgeInfo:kr,BadgeJapaneseYen:Cr,BadgeMinus:Sr,BadgePercent:Lr,BadgePlus:Ar,BadgePoundSterling:Hr,BadgeRussianRuble:Vr,BadgeSwissFranc:Pr,BadgeX:Dr,BaggageClaim:Tr,Ban:Br,Banana:Or,Banknote:Er,BarChart:Nr,BarChart2:Rr,BarChart3:zr,BarChart4:Ir,BarChartBig:$r,BarChartHorizontal:Wr,BarChartHorizontalBig:Zr,Barcode:jr,Baseline:Ur,Bath:qr,Battery:Qr,BatteryCharging:Gr,BatteryFull:Xr,BatteryLow:Yr,BatteryMedium:Kr,BatteryWarning:Jr,Beaker:t0,Bean:s0,BeanOff:e0,Bed:n0,BedDouble:a0,BedSingle:i0,Beef:o0,Beer:r0,Bell:g0,BellDot:h0,BellMinus:c0,BellOff:l0,BellPlus:d0,BellRing:p0,Bike:u0,Binary:f0,Biohazard:v0,Bird:x0,Bitcoin:m0,Blinds:M0,Blocks:y0,Bluetooth:k0,BluetoothConnected:b0,BluetoothOff:w0,BluetoothSearching:_0,Bold:C0,Bomb:S0,Bone:L0,Book:Y0,BookA:A0,BookAudio:H0,BookCheck:V0,BookCopy:P0,BookDashed:Bs,BookDown:D0,BookHeadphones:F0,BookHeart:T0,BookImage:B0,BookKey:O0,BookLock:E0,BookMarked:R0,BookMinus:z0,BookOpen:Z0,BookOpenCheck:I0,BookOpenText:$0,BookPlus:W0,BookTemplate:Bs,BookText:N0,BookType:j0,BookUp:q0,BookUp2:U0,BookUser:G0,BookX:X0,Bookmark:eh,BookmarkCheck:K0,BookmarkMinus:J0,BookmarkPlus:Q0,BookmarkX:th,BoomBox:sh,Bot:ah,Box:nh,BoxSelect:ih,Boxes:oh,Braces:Os,Brackets:rh,Brain:lh,BrainCircuit:hh,BrainCog:ch,Briefcase:dh,BringToFront:ph,Brush:gh,Bug:vh,BugOff:uh,BugPlay:fh,Building:mh,Building2:xh,Bus:yh,BusFront:Mh,Cable:wh,CableCar:bh,Cake:kh,CakeSlice:_h,Calculator:Ch,Calendar:Rh,CalendarCheck:Lh,CalendarCheck2:Sh,CalendarClock:Ah,CalendarDays:Hh,CalendarHeart:Vh,CalendarMinus:Ph,CalendarOff:Dh,CalendarPlus:Fh,CalendarRange:Th,CalendarSearch:Bh,CalendarX:Eh,CalendarX2:Oh,Camera:Ih,CameraOff:zh,CandlestickChart:$h,Candy:Nh,CandyCane:Zh,CandyOff:Wh,Car:qh,CarFront:jh,CarTaxiFront:Uh,Caravan:Gh,Carrot:Xh,CaseLower:Yh,CaseSensitive:Kh,CaseUpper:Jh,CassetteTape:Qh,Cast:tc,Castle:ec,Cat:sc,Check:hc,CheckCheck:ac,CheckCircle:nc,CheckCircle2:ic,CheckSquare:rc,CheckSquare2:oc,ChefHat:cc,Cherry:lc,ChevronDown:gc,ChevronDownCircle:dc,ChevronDownSquare:pc,ChevronFirst:uc,ChevronLast:fc,ChevronLeft:mc,ChevronLeftCircle:vc,ChevronLeftSquare:xc,ChevronRight:bc,ChevronRightCircle:Mc,ChevronRightSquare:yc,ChevronUp:kc,ChevronUpCircle:wc,ChevronUpSquare:_c,ChevronsDown:Sc,ChevronsDownUp:Cc,ChevronsLeft:Ac,ChevronsLeftRight:Lc,ChevronsRight:Vc,ChevronsRightLeft:Hc,ChevronsUp:Dc,ChevronsUpDown:Pc,Chrome:Fc,Church:Tc,Cigarette:Oc,CigaretteOff:Bc,Circle:jc,CircleDashed:Ec,CircleDollarSign:Rc,CircleDot:Ic,CircleDotDashed:zc,CircleEllipsis:$c,CircleEqual:Zc,CircleOff:Wc,CircleSlash:Nc,CircleSlash2:Es,CircleSlashed:Es,CircleUser:zs,CircleUserRound:Rs,CircuitBoard:Uc,Citrus:qc,Clapperboard:Gc,Clipboard:al,ClipboardCheck:Xc,ClipboardCopy:Yc,ClipboardEdit:Kc,ClipboardList:Jc,ClipboardPaste:Qc,ClipboardSignature:tl,ClipboardType:el,ClipboardX:sl,Clock:vl,Clock1:il,Clock10:nl,Clock11:ol,Clock12:rl,Clock2:hl,Clock3:cl,Clock4:ll,Clock5:dl,Clock6:pl,Clock7:gl,Clock8:ul,Clock9:fl,Cloud:Vl,CloudCog:xl,CloudDrizzle:ml,CloudFog:Ml,CloudHail:yl,CloudLightning:bl,CloudMoon:_l,CloudMoonRain:wl,CloudOff:kl,CloudRain:Sl,CloudRainWind:Cl,CloudSnow:Ll,CloudSun:Hl,CloudSunRain:Al,Cloudy:Pl,Clover:Dl,Club:Fl,Code:Bl,Code2:Tl,Codepen:Ol,Codesandbox:El,Coffee:Rl,Cog:zl,Coins:Il,Columns:$l,Combine:Zl,Command:Wl,Compass:Nl,Component:jl,Computer:Ul,ConciergeBell:ql,Cone:Gl,Construction:Xl,Contact:Kl,Contact2:Yl,Container:Jl,Contrast:Ql,Cookie:td,Copy:od,CopyCheck:ed,CopyMinus:sd,CopyPlus:ad,CopySlash:id,CopyX:nd,Copyleft:rd,Copyright:hd,CornerDownLeft:cd,CornerDownRight:ld,CornerLeftDown:dd,CornerLeftUp:pd,CornerRightDown:gd,CornerRightUp:ud,CornerUpLeft:fd,CornerUpRight:vd,Cpu:xd,CreativeCommons:md,CreditCard:Md,Croissant:yd,Crop:bd,Cross:wd,Crosshair:_d,Crown:kd,Cuboid:Cd,CupSoda:Sd,CurlyBraces:Os,Currency:Ld,Cylinder:Ad,Database:Pd,DatabaseBackup:Hd,DatabaseZap:Vd,Delete:Dd,Dessert:Fd,Diameter:Td,Diamond:Bd,Dice1:Od,Dice2:Ed,Dice3:Rd,Dice4:zd,Dice5:Id,Dice6:$d,Dices:Zd,Diff:Wd,Disc:qd,Disc2:Nd,Disc3:jd,DiscAlbum:Ud,Divide:Yd,DivideCircle:Gd,DivideSquare:Xd,Dna:Jd,DnaOff:Kd,Dog:Qd,DollarSign:tp,Donut:ep,DoorClosed:sp,DoorOpen:ap,Dot:ip,Download:op,DownloadCloud:np,DraftingCompass:rp,Drama:hp,Dribbble:cp,Droplet:lp,Droplets:dp,Drum:pp,Drumstick:gp,Dumbbell:up,Ear:vp,EarOff:fp,Edit:V1,Edit2:ta,Edit3:Qs,Egg:Mp,EggFried:xp,EggOff:mp,Equal:bp,EqualNot:yp,Eraser:wp,Euro:_p,Expand:kp,ExternalLink:Cp,Eye:Lp,EyeOff:Sp,Facebook:Ap,Factory:Hp,Fan:Vp,FastForward:Pp,Feather:Dp,FerrisWheel:Fp,Figma:Tp,File:B4,FileArchive:Bp,FileAudio:Ep,FileAudio2:Op,FileAxis3D:Is,FileAxis3d:Is,FileBadge:zp,FileBadge2:Rp,FileBarChart:$p,FileBarChart2:Ip,FileBox:Zp,FileCheck:Np,FileCheck2:Wp,FileClock:jp,FileCode:qp,FileCode2:Up,FileCog:$s,FileCog2:$s,FileDiff:Gp,FileDigit:Xp,FileDown:Yp,FileEdit:Kp,FileHeart:Jp,FileImage:Qp,FileInput:t4,FileJson:s4,FileJson2:e4,FileKey:i4,FileKey2:a4,FileLineChart:n4,FileLock:r4,FileLock2:o4,FileMinus:c4,FileMinus2:h4,FileMusic:l4,FileOutput:d4,FilePieChart:p4,FilePlus:u4,FilePlus2:g4,FileQuestion:f4,FileScan:v4,FileSearch:m4,FileSearch2:x4,FileSignature:M4,FileSpreadsheet:y4,FileStack:b4,FileSymlink:w4,FileTerminal:_4,FileText:k4,FileType:S4,FileType2:C4,FileUp:L4,FileVideo:H4,FileVideo2:A4,FileVolume:P4,FileVolume2:V4,FileWarning:D4,FileX:T4,FileX2:F4,Files:O4,Film:E4,Filter:z4,FilterX:R4,Fingerprint:I4,Fish:W4,FishOff:$4,FishSymbol:Z4,Flag:q4,FlagOff:N4,FlagTriangleLeft:j4,FlagTriangleRight:U4,Flame:X4,FlameKindling:G4,Flashlight:K4,FlashlightOff:Y4,FlaskConical:Q4,FlaskConicalOff:J4,FlaskRound:t5,FlipHorizontal:s5,FlipHorizontal2:e5,FlipVertical:i5,FlipVertical2:a5,Flower:o5,Flower2:n5,Focus:r5,FoldHorizontal:h5,FoldVertical:c5,Folder:E5,FolderArchive:l5,FolderCheck:d5,FolderClock:p5,FolderClosed:g5,FolderCog:Zs,FolderCog2:Zs,FolderDot:u5,FolderDown:f5,FolderEdit:v5,FolderGit:m5,FolderGit2:x5,FolderHeart:M5,FolderInput:y5,FolderKanban:b5,FolderKey:w5,FolderLock:_5,FolderMinus:k5,FolderOpen:S5,FolderOpenDot:C5,FolderOutput:L5,FolderPlus:A5,FolderRoot:H5,FolderSearch:P5,FolderSearch2:V5,FolderSymlink:D5,FolderSync:F5,FolderTree:T5,FolderUp:B5,FolderX:O5,Folders:R5,Footprints:z5,Forklift:I5,FormInput:$5,Forward:Z5,Frame:W5,Framer:N5,Frown:j5,Fuel:U5,Fullscreen:q5,FunctionSquare:G5,GalleryHorizontal:Y5,GalleryHorizontalEnd:X5,GalleryThumbnails:K5,GalleryVertical:Q5,GalleryVerticalEnd:J5,Gamepad:eg,Gamepad2:tg,GanttChart:sg,GanttChartSquare:Ws,Gauge:ig,GaugeCircle:ag,Gavel:ng,Gem:og,Ghost:rg,Gift:hg,GitBranch:lg,GitBranchPlus:cg,GitCommit:Ns,GitCommitHorizontal:Ns,GitCommitVertical:dg,GitCompare:gg,GitCompareArrows:pg,GitFork:ug,GitGraph:fg,GitMerge:vg,GitPullRequest:wg,GitPullRequestArrow:xg,GitPullRequestClosed:mg,GitPullRequestCreate:yg,GitPullRequestCreateArrow:Mg,GitPullRequestDraft:bg,Github:_g,Gitlab:kg,GlassWater:Cg,Glasses:Sg,Globe:Ag,Globe2:Lg,Goal:Hg,Grab:Vg,GraduationCap:Pg,Grape:Dg,Grid:H1,Grid2X2:js,Grid2x2:js,Grid3X3:H1,Grid3x3:H1,Grip:Bg,GripHorizontal:Fg,GripVertical:Tg,Group:Og,Guitar:Eg,Hammer:Rg,Hand:Ig,HandMetal:zg,HardDrive:Wg,HardDriveDownload:$g,HardDriveUpload:Zg,HardHat:Ng,Hash:jg,Haze:Ug,HdmiPort:qg,Heading:tu,Heading1:Gg,Heading2:Xg,Heading3:Yg,Heading4:Kg,Heading5:Jg,Heading6:Qg,Headphones:eu,Heart:ou,HeartCrack:su,HeartHandshake:au,HeartOff:iu,HeartPulse:nu,HelpCircle:ru,HelpingHand:hu,Hexagon:cu,Highlighter:lu,History:du,Home:pu,Hop:uu,HopOff:gu,Hotel:fu,Hourglass:vu,IceCream:mu,IceCream2:xu,Image:_u,ImageDown:Mu,ImageMinus:yu,ImageOff:bu,ImagePlus:wu,Import:ku,Inbox:Cu,Indent:Su,IndianRupee:Lu,Infinity:Au,Info:Hu,Inspect:Gs,Instagram:Vu,Italic:Pu,IterationCcw:Du,IterationCw:Fu,JapaneseYen:Tu,Joystick:Bu,Kanban:Ou,KanbanSquare:qs,KanbanSquareDashed:Us,Key:zu,KeyRound:Eu,KeySquare:Ru,Keyboard:$u,KeyboardMusic:Iu,Lamp:qu,LampCeiling:Zu,LampDesk:Wu,LampFloor:Nu,LampWallDown:ju,LampWallUp:Uu,LandPlot:Gu,Landmark:Xu,Languages:Yu,Laptop:Ju,Laptop2:Ku,Lasso:t3,LassoSelect:Qu,Laugh:e3,Layers:i3,Layers2:s3,Layers3:a3,Layout:d3,LayoutDashboard:n3,LayoutGrid:o3,LayoutList:r3,LayoutPanelLeft:h3,LayoutPanelTop:c3,LayoutTemplate:l3,Leaf:p3,LeafyGreen:g3,Library:v3,LibraryBig:u3,LibrarySquare:f3,LifeBuoy:x3,Ligature:m3,Lightbulb:y3,LightbulbOff:M3,LineChart:b3,Link:k3,Link2:_3,Link2Off:w3,Linkedin:C3,List:z3,ListChecks:S3,ListEnd:L3,ListFilter:A3,ListMinus:H3,ListMusic:V3,ListOrdered:P3,ListPlus:D3,ListRestart:F3,ListStart:T3,ListTodo:B3,ListTree:O3,ListVideo:E3,ListX:R3,Loader:$3,Loader2:I3,Locate:N3,LocateFixed:Z3,LocateOff:W3,Lock:U3,LockKeyhole:j3,LogIn:q3,LogOut:G3,Lollipop:X3,Luggage:Y3,MSquare:K3,Magnet:J3,Mail:hf,MailCheck:Q3,MailMinus:tf,MailOpen:ef,MailPlus:sf,MailQuestion:af,MailSearch:nf,MailWarning:of,MailX:rf,Mailbox:cf,Mails:lf,Map:uf,MapPin:pf,MapPinOff:df,MapPinned:gf,Martini:ff,Maximize:xf,Maximize2:vf,Medal:mf,Megaphone:yf,MegaphoneOff:Mf,Meh:bf,MemoryStick:wf,Menu:kf,MenuSquare:_f,Merge:Cf,MessageCircle:Sf,MessageSquare:Hf,MessageSquareDashed:Lf,MessageSquarePlus:Af,MessagesSquare:Vf,Mic:Ff,Mic2:Pf,MicOff:Df,Microscope:Tf,Microwave:Bf,Milestone:Of,Milk:Rf,MilkOff:Ef,Minimize:If,Minimize2:zf,Minus:Wf,MinusCircle:$f,MinusSquare:Zf,Monitor:e6,MonitorCheck:Nf,MonitorDot:jf,MonitorDown:Uf,MonitorOff:qf,MonitorPause:Gf,MonitorPlay:Xf,MonitorSmartphone:Yf,MonitorSpeaker:Kf,MonitorStop:Jf,MonitorUp:Qf,MonitorX:t6,Moon:a6,MoonStar:s6,MoreHorizontal:i6,MoreVertical:n6,Mountain:r6,MountainSnow:o6,Mouse:p6,MousePointer:d6,MousePointer2:h6,MousePointerClick:c6,MousePointerSquare:Gs,MousePointerSquareDashed:l6,Move:C6,Move3D:Xs,Move3d:Xs,MoveDiagonal:u6,MoveDiagonal2:g6,MoveDown:x6,MoveDownLeft:f6,MoveDownRight:v6,MoveHorizontal:m6,MoveLeft:M6,MoveRight:y6,MoveUp:_6,MoveUpLeft:b6,MoveUpRight:w6,MoveVertical:k6,Music:H6,Music2:S6,Music3:L6,Music4:A6,Navigation:F6,Navigation2:P6,Navigation2Off:V6,NavigationOff:D6,Network:T6,Newspaper:B6,Nfc:O6,Nut:R6,NutOff:E6,Octagon:z6,Option:I6,Orbit:$6,Outdent:Z6,Package:Y6,Package2:W6,PackageCheck:N6,PackageMinus:j6,PackageOpen:U6,PackagePlus:q6,PackageSearch:G6,PackageX:X6,PaintBucket:K6,Paintbrush:Q6,Paintbrush2:J6,Palette:tv,Palmtree:ev,PanelBottom:nv,PanelBottomClose:sv,PanelBottomInactive:av,PanelBottomOpen:iv,PanelLeft:Js,PanelLeftClose:Ys,PanelLeftInactive:ov,PanelLeftOpen:Ks,PanelRight:lv,PanelRightClose:rv,PanelRightInactive:hv,PanelRightOpen:cv,PanelTop:uv,PanelTopClose:dv,PanelTopInactive:pv,PanelTopOpen:gv,Paperclip:fv,Parentheses:vv,ParkingCircle:mv,ParkingCircleOff:xv,ParkingMeter:Mv,ParkingSquare:bv,ParkingSquareOff:yv,PartyPopper:wv,Pause:Cv,PauseCircle:_v,PauseOctagon:kv,PawPrint:Sv,PcCase:Lv,Pen:ta,PenBox:V1,PenLine:Qs,PenSquare:V1,PenTool:Av,Pencil:Pv,PencilLine:Hv,PencilRuler:Vv,Pentagon:Dv,Percent:Ov,PercentCircle:Fv,PercentDiamond:Tv,PercentSquare:Bv,PersonStanding:Ev,Phone:Nv,PhoneCall:Rv,PhoneForwarded:zv,PhoneIncoming:Iv,PhoneMissed:$v,PhoneOff:Zv,PhoneOutgoing:Wv,Pi:Uv,PiSquare:jv,Piano:qv,PictureInPicture:Xv,PictureInPicture2:Gv,PieChart:Yv,PiggyBank:Kv,Pilcrow:Qv,PilcrowSquare:Jv,Pill:t8,Pin:s8,PinOff:e8,Pipette:a8,Pizza:i8,Plane:r8,PlaneLanding:n8,PlaneTakeoff:o8,Play:l8,PlayCircle:h8,PlaySquare:c8,Plug:u8,Plug2:d8,PlugZap:g8,PlugZap2:p8,Plus:x8,PlusCircle:f8,PlusSquare:v8,Pocket:M8,PocketKnife:m8,Podcast:y8,Pointer:b8,Popcorn:w8,Popsicle:_8,PoundSterling:k8,Power:A8,PowerCircle:C8,PowerOff:S8,PowerSquare:L8,Presentation:H8,Printer:V8,Projector:P8,Puzzle:D8,Pyramid:F8,QrCode:T8,Quote:B8,Rabbit:O8,Radar:E8,Radiation:R8,Radio:$8,RadioReceiver:z8,RadioTower:I8,Radius:Z8,RailSymbol:W8,Rainbow:N8,Rat:j8,Ratio:U8,Receipt:q8,RectangleHorizontal:G8,RectangleVertical:X8,Recycle:Y8,Redo:Q8,Redo2:K8,RedoDot:J8,RefreshCcw:ex,RefreshCcwDot:tx,RefreshCw:ax,RefreshCwOff:sx,Refrigerator:ix,Regex:nx,RemoveFormatting:ox,Repeat:cx,Repeat1:rx,Repeat2:hx,Replace:dx,ReplaceAll:lx,Reply:gx,ReplyAll:px,Rewind:ux,Ribbon:fx,Rocket:vx,RockingChair:xx,RollerCoaster:mx,Rotate3D:ea,Rotate3d:ea,RotateCcw:Mx,RotateCw:yx,Route:wx,RouteOff:bx,Router:_x,Rows:kx,Rss:Cx,Ruler:Sx,RussianRuble:Lx,Sailboat:Ax,Salad:Hx,Sandwich:Vx,Satellite:Dx,SatelliteDish:Px,Save:Tx,SaveAll:Fx,Scale:Bx,Scale3D:sa,Scale3d:sa,Scaling:Ox,Scan:Wx,ScanBarcode:Ex,ScanEye:Rx,ScanFace:zx,ScanLine:Ix,ScanSearch:$x,ScanText:Zx,ScatterChart:Nx,School:Ux,School2:jx,Scissors:Yx,ScissorsLineDashed:qx,ScissorsSquare:Xx,ScissorsSquareDashedBottom:Gx,ScreenShare:Jx,ScreenShareOff:Kx,Scroll:tm,ScrollText:Qx,Search:nm,SearchCheck:em,SearchCode:sm,SearchSlash:am,SearchX:im,Send:rm,SendHorizonal:aa,SendHorizontal:aa,SendToBack:om,SeparatorHorizontal:hm,SeparatorVertical:cm,Server:gm,ServerCog:lm,ServerCrash:dm,ServerOff:pm,Settings:fm,Settings2:um,Shapes:vm,Share:mm,Share2:xm,Sheet:Mm,Shell:ym,Shield:Vm,ShieldAlert:bm,ShieldBan:wm,ShieldCheck:_m,ShieldClose:ia,ShieldEllipsis:km,ShieldHalf:Cm,ShieldMinus:Sm,ShieldOff:Lm,ShieldPlus:Am,ShieldQuestion:Hm,ShieldX:ia,Ship:Dm,ShipWheel:Pm,Shirt:Fm,ShoppingBag:Tm,ShoppingBasket:Bm,ShoppingCart:Om,Shovel:Em,ShowerHead:Rm,Shrink:zm,Shrub:Im,Shuffle:$m,Sidebar:Js,SidebarClose:Ys,SidebarOpen:Ks,Sigma:Wm,SigmaSquare:Zm,Signal:Gm,SignalHigh:Nm,SignalLow:jm,SignalMedium:Um,SignalZero:qm,Signpost:Ym,SignpostBig:Xm,Siren:Km,SkipBack:Jm,SkipForward:Qm,Skull:tM,Slack:eM,Slash:sM,Slice:aM,Sliders:nM,SlidersHorizontal:iM,Smartphone:hM,SmartphoneCharging:oM,SmartphoneNfc:rM,Smile:lM,SmilePlus:cM,Snail:dM,Snowflake:pM,Sofa:gM,SortAsc:Ps,SortDesc:As,Soup:uM,Space:fM,Spade:vM,Sparkle:xM,Sparkles:na,Speaker:mM,Speech:MM,SpellCheck:bM,SpellCheck2:yM,Spline:wM,Split:CM,SplitSquareHorizontal:_M,SplitSquareVertical:kM,SprayCan:SM,Sprout:LM,Square:OM,SquareAsterisk:AM,SquareCode:HM,SquareDashedBottom:PM,SquareDashedBottomCode:VM,SquareDot:DM,SquareEqual:FM,SquareGantt:Ws,SquareKanban:qs,SquareKanbanDashed:Us,SquareSlash:TM,SquareStack:BM,SquareUser:ra,SquareUserRound:oa,Squirrel:EM,Stamp:RM,Star:$M,StarHalf:zM,StarOff:IM,Stars:na,StepBack:ZM,StepForward:WM,Stethoscope:NM,Sticker:jM,StickyNote:UM,StopCircle:qM,Store:GM,StretchHorizontal:XM,StretchVertical:YM,Strikethrough:KM,Subscript:JM,Subtitles:QM,Sun:i7,SunDim:t7,SunMedium:e7,SunMoon:s7,SunSnow:a7,Sunrise:n7,Sunset:o7,Superscript:r7,SwissFranc:h7,SwitchCamera:c7,Sword:l7,Swords:d7,Syringe:p7,Table:f7,Table2:g7,TableProperties:u7,Tablet:x7,TabletSmartphone:v7,Tablets:m7,Tag:M7,Tags:y7,Tally1:b7,Tally2:w7,Tally3:_7,Tally4:k7,Tally5:C7,Tangent:S7,Target:L7,Tent:H7,TentTree:A7,Terminal:P7,TerminalSquare:V7,TestTube:F7,TestTube2:D7,TestTubes:T7,Text:R7,TextCursor:O7,TextCursorInput:B7,TextQuote:E7,TextSelect:ha,TextSelection:ha,Theater:z7,Thermometer:Z7,ThermometerSnowflake:I7,ThermometerSun:$7,ThumbsDown:W7,ThumbsUp:N7,Ticket:j7,Timer:G7,TimerOff:U7,TimerReset:q7,ToggleLeft:X7,ToggleRight:Y7,Tornado:K7,Torus:J7,Touchpad:ty,TouchpadOff:Q7,TowerControl:ey,ToyBrick:sy,Tractor:ay,TrafficCone:iy,Train:ca,TrainFront:oy,TrainFrontTunnel:ny,TrainTrack:ry,TramFront:ca,Trash:cy,Trash2:hy,TreeDeciduous:ly,TreePine:dy,Trees:py,Trello:gy,TrendingDown:uy,TrendingUp:fy,Triangle:xy,TriangleRight:vy,Trophy:my,Truck:My,Turtle:yy,Tv:wy,Tv2:by,Twitch:_y,Twitter:ky,Type:Cy,Umbrella:Ly,UmbrellaOff:Sy,Underline:Ay,Undo:Py,Undo2:Hy,UndoDot:Vy,UnfoldHorizontal:Dy,UnfoldVertical:Fy,Ungroup:Ty,Unlink:Oy,Unlink2:By,Unlock:Ry,UnlockKeyhole:Ey,Unplug:zy,Upload:$y,UploadCloud:Iy,Usb:Zy,User:Gy,User2:fa,UserCheck:Wy,UserCheck2:la,UserCircle:zs,UserCircle2:Rs,UserCog:Ny,UserCog2:da,UserMinus:jy,UserMinus2:pa,UserPlus:Uy,UserPlus2:ga,UserRound:fa,UserRoundCheck:la,UserRoundCog:da,UserRoundMinus:pa,UserRoundPlus:ga,UserRoundX:ua,UserSquare:ra,UserSquare2:oa,UserX:qy,UserX2:ua,Users:Xy,Users2:va,UsersRound:va,Utensils:Ky,UtensilsCrossed:Yy,UtilityPole:Jy,Variable:Qy,Vegan:t9,VenetianMask:e9,Verified:Ts,Vibrate:a9,VibrateOff:s9,Video:n9,VideoOff:i9,Videotape:o9,View:r9,Voicemail:h9,Volume:p9,Volume1:c9,Volume2:l9,VolumeX:d9,Vote:g9,Wallet:v9,Wallet2:u9,WalletCards:f9,Wallpaper:x9,Wand:M9,Wand2:m9,Warehouse:y9,Watch:b9,Waves:w9,Waypoints:_9,Webcam:k9,Webhook:C9,Weight:S9,Wheat:A9,WheatOff:L9,WholeWord:H9,Wifi:P9,WifiOff:V9,Wind:D9,Wine:T9,WineOff:F9,Workflow:B9,WrapText:O9,Wrench:E9,X:$9,XCircle:R9,XOctagon:z9,XSquare:I9,Youtube:Z9,Zap:N9,ZapOff:W9,ZoomIn:j9,ZoomOut:U9},Symbol.toStringTag,{value:"Module"}));/**
 * @license lucide v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G9=({icons:s={},nameAttr:t="data-lucide",attrs:e={}}={})=>{if(!Object.values(s).length)throw new Error(`Please provide an icons object.
If you want to use all the icons you can import it like:
 \`import { createIcons, icons } from 'lucide';
lucide.createIcons({icons});\``);if(typeof document>"u")throw new Error("`createIcons()` only works in a browser environment.");const a=document.querySelectorAll(`[${t}]`);if(Array.from(a).forEach(i=>Cs(i,{nameAttr:t,icons:s,attrs:e})),t==="data-lucide"){const i=document.querySelectorAll("[icon-name]");i.length>0&&(console.warn("[Lucide] Some icons were found with the now deprecated icon-name attribute. These will still be replaced for backwards compatibility, but will no longer be supported in v1.0 and you should switch to data-lucide"),Array.from(i).forEach(n=>Cs(n,{nameAttr:"icon-name",icons:s,attrs:e})))}};function X9(){G9({icons:q9})}/*!
 * @kurkle/color v0.3.4
 * https://github.com/kurkle/color#readme
 * (c) 2024 Jukka Kurkela
 * Released under the MIT License
 */function Ie(s){return s+.5|0}const St=(s,t,e)=>Math.max(Math.min(s,e),t);function xe(s){return St(Ie(s*2.55),0,255)}function Vt(s){return St(Ie(s*255),0,255)}function bt(s){return St(Ie(s/2.55)/100,0,1)}function xa(s){return St(Ie(s*100),0,100)}const rt={0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,A:10,B:11,C:12,D:13,E:14,F:15,a:10,b:11,c:12,d:13,e:14,f:15},U1=[..."0123456789ABCDEF"],Y9=s=>U1[s&15],K9=s=>U1[(s&240)>>4]+U1[s&15],Ne=s=>(s&240)>>4===(s&15),J9=s=>Ne(s.r)&&Ne(s.g)&&Ne(s.b)&&Ne(s.a);function Q9(s){var t=s.length,e;return s[0]==="#"&&(t===4||t===5?e={r:255&rt[s[1]]*17,g:255&rt[s[2]]*17,b:255&rt[s[3]]*17,a:t===5?rt[s[4]]*17:255}:(t===7||t===9)&&(e={r:rt[s[1]]<<4|rt[s[2]],g:rt[s[3]]<<4|rt[s[4]],b:rt[s[5]]<<4|rt[s[6]],a:t===9?rt[s[7]]<<4|rt[s[8]]:255})),e}const tb=(s,t)=>s<255?t(s):"";function eb(s){var t=J9(s)?Y9:K9;return s?"#"+t(s.r)+t(s.g)+t(s.b)+tb(s.a,t):void 0}const sb=/^(hsla?|hwb|hsv)\(\s*([-+.e\d]+)(?:deg)?[\s,]+([-+.e\d]+)%[\s,]+([-+.e\d]+)%(?:[\s,]+([-+.e\d]+)(%)?)?\s*\)$/;function W2(s,t,e){const a=t*Math.min(e,1-e),i=(n,r=(n+s/30)%12)=>e-a*Math.max(Math.min(r-3,9-r,1),-1);return[i(0),i(8),i(4)]}function ab(s,t,e){const a=(i,n=(i+s/60)%6)=>e-e*t*Math.max(Math.min(n,4-n,1),0);return[a(5),a(3),a(1)]}function ib(s,t,e){const a=W2(s,1,.5);let i;for(t+e>1&&(i=1/(t+e),t*=i,e*=i),i=0;i<3;i++)a[i]*=1-t-e,a[i]+=t;return a}function nb(s,t,e,a,i){return s===i?(t-e)/a+(t<e?6:0):t===i?(e-s)/a+2:(s-t)/a+4}function os(s){const e=s.r/255,a=s.g/255,i=s.b/255,n=Math.max(e,a,i),r=Math.min(e,a,i),h=(n+r)/2;let c,l,d;return n!==r&&(d=n-r,l=h>.5?d/(2-n-r):d/(n+r),c=nb(e,a,i,d,n),c=c*60+.5),[c|0,l||0,h]}function rs(s,t,e,a){return(Array.isArray(t)?s(t[0],t[1],t[2]):s(t,e,a)).map(Vt)}function hs(s,t,e){return rs(W2,s,t,e)}function ob(s,t,e){return rs(ib,s,t,e)}function rb(s,t,e){return rs(ab,s,t,e)}function N2(s){return(s%360+360)%360}function hb(s){const t=sb.exec(s);let e=255,a;if(!t)return;t[5]!==a&&(e=t[6]?xe(+t[5]):Vt(+t[5]));const i=N2(+t[2]),n=+t[3]/100,r=+t[4]/100;return t[1]==="hwb"?a=ob(i,n,r):t[1]==="hsv"?a=rb(i,n,r):a=hs(i,n,r),{r:a[0],g:a[1],b:a[2],a:e}}function cb(s,t){var e=os(s);e[0]=N2(e[0]+t),e=hs(e),s.r=e[0],s.g=e[1],s.b=e[2]}function lb(s){if(!s)return;const t=os(s),e=t[0],a=xa(t[1]),i=xa(t[2]);return s.a<255?`hsla(${e}, ${a}%, ${i}%, ${bt(s.a)})`:`hsl(${e}, ${a}%, ${i}%)`}const ma={x:"dark",Z:"light",Y:"re",X:"blu",W:"gr",V:"medium",U:"slate",A:"ee",T:"ol",S:"or",B:"ra",C:"lateg",D:"ights",R:"in",Q:"turquois",E:"hi",P:"ro",O:"al",N:"le",M:"de",L:"yello",F:"en",K:"ch",G:"arks",H:"ea",I:"ightg",J:"wh"},Ma={OiceXe:"f0f8ff",antiquewEte:"faebd7",aqua:"ffff",aquamarRe:"7fffd4",azuY:"f0ffff",beige:"f5f5dc",bisque:"ffe4c4",black:"0",blanKedOmond:"ffebcd",Xe:"ff",XeviTet:"8a2be2",bPwn:"a52a2a",burlywood:"deb887",caMtXe:"5f9ea0",KartYuse:"7fff00",KocTate:"d2691e",cSO:"ff7f50",cSnflowerXe:"6495ed",cSnsilk:"fff8dc",crimson:"dc143c",cyan:"ffff",xXe:"8b",xcyan:"8b8b",xgTMnPd:"b8860b",xWay:"a9a9a9",xgYF:"6400",xgYy:"a9a9a9",xkhaki:"bdb76b",xmagFta:"8b008b",xTivegYF:"556b2f",xSange:"ff8c00",xScEd:"9932cc",xYd:"8b0000",xsOmon:"e9967a",xsHgYF:"8fbc8f",xUXe:"483d8b",xUWay:"2f4f4f",xUgYy:"2f4f4f",xQe:"ced1",xviTet:"9400d3",dAppRk:"ff1493",dApskyXe:"bfff",dimWay:"696969",dimgYy:"696969",dodgerXe:"1e90ff",fiYbrick:"b22222",flSOwEte:"fffaf0",foYstWAn:"228b22",fuKsia:"ff00ff",gaRsbSo:"dcdcdc",ghostwEte:"f8f8ff",gTd:"ffd700",gTMnPd:"daa520",Way:"808080",gYF:"8000",gYFLw:"adff2f",gYy:"808080",honeyMw:"f0fff0",hotpRk:"ff69b4",RdianYd:"cd5c5c",Rdigo:"4b0082",ivSy:"fffff0",khaki:"f0e68c",lavFMr:"e6e6fa",lavFMrXsh:"fff0f5",lawngYF:"7cfc00",NmoncEffon:"fffacd",ZXe:"add8e6",ZcSO:"f08080",Zcyan:"e0ffff",ZgTMnPdLw:"fafad2",ZWay:"d3d3d3",ZgYF:"90ee90",ZgYy:"d3d3d3",ZpRk:"ffb6c1",ZsOmon:"ffa07a",ZsHgYF:"20b2aa",ZskyXe:"87cefa",ZUWay:"778899",ZUgYy:"778899",ZstAlXe:"b0c4de",ZLw:"ffffe0",lime:"ff00",limegYF:"32cd32",lRF:"faf0e6",magFta:"ff00ff",maPon:"800000",VaquamarRe:"66cdaa",VXe:"cd",VScEd:"ba55d3",VpurpN:"9370db",VsHgYF:"3cb371",VUXe:"7b68ee",VsprRggYF:"fa9a",VQe:"48d1cc",VviTetYd:"c71585",midnightXe:"191970",mRtcYam:"f5fffa",mistyPse:"ffe4e1",moccasR:"ffe4b5",navajowEte:"ffdead",navy:"80",Tdlace:"fdf5e6",Tive:"808000",TivedBb:"6b8e23",Sange:"ffa500",SangeYd:"ff4500",ScEd:"da70d6",pOegTMnPd:"eee8aa",pOegYF:"98fb98",pOeQe:"afeeee",pOeviTetYd:"db7093",papayawEp:"ffefd5",pHKpuff:"ffdab9",peru:"cd853f",pRk:"ffc0cb",plum:"dda0dd",powMrXe:"b0e0e6",purpN:"800080",YbeccapurpN:"663399",Yd:"ff0000",Psybrown:"bc8f8f",PyOXe:"4169e1",saddNbPwn:"8b4513",sOmon:"fa8072",sandybPwn:"f4a460",sHgYF:"2e8b57",sHshell:"fff5ee",siFna:"a0522d",silver:"c0c0c0",skyXe:"87ceeb",UXe:"6a5acd",UWay:"708090",UgYy:"708090",snow:"fffafa",sprRggYF:"ff7f",stAlXe:"4682b4",tan:"d2b48c",teO:"8080",tEstN:"d8bfd8",tomato:"ff6347",Qe:"40e0d0",viTet:"ee82ee",JHt:"f5deb3",wEte:"ffffff",wEtesmoke:"f5f5f5",Lw:"ffff00",LwgYF:"9acd32"};function db(){const s={},t=Object.keys(Ma),e=Object.keys(ma);let a,i,n,r,h;for(a=0;a<t.length;a++){for(r=h=t[a],i=0;i<e.length;i++)n=e[i],h=h.replace(n,ma[n]);n=parseInt(Ma[r],16),s[h]=[n>>16&255,n>>8&255,n&255]}return s}let je;function pb(s){je||(je=db(),je.transparent=[0,0,0,0]);const t=je[s.toLowerCase()];return t&&{r:t[0],g:t[1],b:t[2],a:t.length===4?t[3]:255}}const gb=/^rgba?\(\s*([-+.\d]+)(%)?[\s,]+([-+.e\d]+)(%)?[\s,]+([-+.e\d]+)(%)?(?:[\s,/]+([-+.e\d]+)(%)?)?\s*\)$/;function ub(s){const t=gb.exec(s);let e=255,a,i,n;if(t){if(t[7]!==a){const r=+t[7];e=t[8]?xe(r):St(r*255,0,255)}return a=+t[1],i=+t[3],n=+t[5],a=255&(t[2]?xe(a):St(a,0,255)),i=255&(t[4]?xe(i):St(i,0,255)),n=255&(t[6]?xe(n):St(n,0,255)),{r:a,g:i,b:n,a:e}}}function fb(s){return s&&(s.a<255?`rgba(${s.r}, ${s.g}, ${s.b}, ${bt(s.a)})`:`rgb(${s.r}, ${s.g}, ${s.b})`)}const P1=s=>s<=.0031308?s*12.92:Math.pow(s,1/2.4)*1.055-.055,Qt=s=>s<=.04045?s/12.92:Math.pow((s+.055)/1.055,2.4);function vb(s,t,e){const a=Qt(bt(s.r)),i=Qt(bt(s.g)),n=Qt(bt(s.b));return{r:Vt(P1(a+e*(Qt(bt(t.r))-a))),g:Vt(P1(i+e*(Qt(bt(t.g))-i))),b:Vt(P1(n+e*(Qt(bt(t.b))-n))),a:s.a+e*(t.a-s.a)}}function Ue(s,t,e){if(s){let a=os(s);a[t]=Math.max(0,Math.min(a[t]+a[t]*e,t===0?360:1)),a=hs(a),s.r=a[0],s.g=a[1],s.b=a[2]}}function j2(s,t){return s&&Object.assign(t||{},s)}function ya(s){var t={r:0,g:0,b:0,a:255};return Array.isArray(s)?s.length>=3&&(t={r:s[0],g:s[1],b:s[2],a:255},s.length>3&&(t.a=Vt(s[3]))):(t=j2(s,{r:0,g:0,b:0,a:1}),t.a=Vt(t.a)),t}function xb(s){return s.charAt(0)==="r"?ub(s):hb(s)}class De{constructor(t){if(t instanceof De)return t;const e=typeof t;let a;e==="object"?a=ya(t):e==="string"&&(a=Q9(t)||pb(t)||xb(t)),this._rgb=a,this._valid=!!a}get valid(){return this._valid}get rgb(){var t=j2(this._rgb);return t&&(t.a=bt(t.a)),t}set rgb(t){this._rgb=ya(t)}rgbString(){return this._valid?fb(this._rgb):void 0}hexString(){return this._valid?eb(this._rgb):void 0}hslString(){return this._valid?lb(this._rgb):void 0}mix(t,e){if(t){const a=this.rgb,i=t.rgb;let n;const r=e===n?.5:e,h=2*r-1,c=a.a-i.a,l=((h*c===-1?h:(h+c)/(1+h*c))+1)/2;n=1-l,a.r=255&l*a.r+n*i.r+.5,a.g=255&l*a.g+n*i.g+.5,a.b=255&l*a.b+n*i.b+.5,a.a=r*a.a+(1-r)*i.a,this.rgb=a}return this}interpolate(t,e){return t&&(this._rgb=vb(this._rgb,t._rgb,e)),this}clone(){return new De(this.rgb)}alpha(t){return this._rgb.a=Vt(t),this}clearer(t){const e=this._rgb;return e.a*=1-t,this}greyscale(){const t=this._rgb,e=Ie(t.r*.3+t.g*.59+t.b*.11);return t.r=t.g=t.b=e,this}opaquer(t){const e=this._rgb;return e.a*=1+t,this}negate(){const t=this._rgb;return t.r=255-t.r,t.g=255-t.g,t.b=255-t.b,this}lighten(t){return Ue(this._rgb,2,t),this}darken(t){return Ue(this._rgb,2,-t),this}saturate(t){return Ue(this._rgb,1,t),this}desaturate(t){return Ue(this._rgb,1,-t),this}rotate(t){return cb(this._rgb,t),this}}/*!
 * Chart.js v4.5.1
 * https://www.chartjs.org
 * (c) 2025 Chart.js Contributors
 * Released under the MIT License
 */function mt(){}const mb=(()=>{let s=0;return()=>s++})();function F(s){return s==null}function Z(s){if(Array.isArray&&Array.isArray(s))return!0;const t=Object.prototype.toString.call(s);return t.slice(0,7)==="[object"&&t.slice(-6)==="Array]"}function T(s){return s!==null&&Object.prototype.toString.call(s)==="[object Object]"}function N(s){return(typeof s=="number"||s instanceof Number)&&isFinite(+s)}function ot(s,t){return N(s)?s:t}function H(s,t){return typeof s>"u"?t:s}const Mb=(s,t)=>typeof s=="string"&&s.endsWith("%")?parseFloat(s)/100:+s/t,U2=(s,t)=>typeof s=="string"&&s.endsWith("%")?parseFloat(s)/100*t:+s;function z(s,t,e){if(s&&typeof s.call=="function")return s.apply(e,t)}function E(s,t,e,a){let i,n,r;if(Z(s))for(n=s.length,i=0;i<n;i++)t.call(e,s[i],i);else if(T(s))for(r=Object.keys(s),n=r.length,i=0;i<n;i++)t.call(e,s[r[i]],r[i])}function p1(s,t){let e,a,i,n;if(!s||!t||s.length!==t.length)return!1;for(e=0,a=s.length;e<a;++e)if(i=s[e],n=t[e],i.datasetIndex!==n.datasetIndex||i.index!==n.index)return!1;return!0}function g1(s){if(Z(s))return s.map(g1);if(T(s)){const t=Object.create(null),e=Object.keys(s),a=e.length;let i=0;for(;i<a;++i)t[e[i]]=g1(s[e[i]]);return t}return s}function q2(s){return["__proto__","prototype","constructor"].indexOf(s)===-1}function yb(s,t,e,a){if(!q2(s))return;const i=t[s],n=e[s];T(i)&&T(n)?Fe(i,n,a):t[s]=g1(n)}function Fe(s,t,e){const a=Z(t)?t:[t],i=a.length;if(!T(s))return s;e=e||{};const n=e.merger||yb;let r;for(let h=0;h<i;++h){if(r=a[h],!T(r))continue;const c=Object.keys(r);for(let l=0,d=c.length;l<d;++l)n(c[l],s,r,e)}return s}function ke(s,t){return Fe(s,t,{merger:bb})}function bb(s,t,e){if(!q2(s))return;const a=t[s],i=e[s];T(a)&&T(i)?ke(a,i):Object.prototype.hasOwnProperty.call(t,s)||(t[s]=g1(i))}const ba={"":s=>s,x:s=>s.x,y:s=>s.y};function wb(s){const t=s.split("."),e=[];let a="";for(const i of t)a+=i,a.endsWith("\\")?a=a.slice(0,-1)+".":(e.push(a),a="");return e}function _b(s){const t=wb(s);return e=>{for(const a of t){if(a==="")break;e=e&&e[a]}return e}}function Pt(s,t){return(ba[t]||(ba[t]=_b(t)))(s)}function cs(s){return s.charAt(0).toUpperCase()+s.slice(1)}const Te=s=>typeof s<"u",Dt=s=>typeof s=="function",wa=(s,t)=>{if(s.size!==t.size)return!1;for(const e of s)if(!t.has(e))return!1;return!0};function kb(s){return s.type==="mouseup"||s.type==="click"||s.type==="contextmenu"}const O=Math.PI,I=2*O,Cb=I+O,u1=Number.POSITIVE_INFINITY,Sb=O/180,U=O/2,Ot=O/4,_a=O*2/3,Lt=Math.log10,xt=Math.sign;function Ce(s,t,e){return Math.abs(s-t)<e}function ka(s){const t=Math.round(s);s=Ce(s,t,s/1e3)?t:s;const e=Math.pow(10,Math.floor(Lt(s))),a=s/e;return(a<=1?1:a<=2?2:a<=5?5:10)*e}function Lb(s){const t=[],e=Math.sqrt(s);let a;for(a=1;a<e;a++)s%a===0&&(t.push(a),t.push(s/a));return e===(e|0)&&t.push(e),t.sort((i,n)=>i-n).pop(),t}function Ab(s){return typeof s=="symbol"||typeof s=="object"&&s!==null&&!(Symbol.toPrimitive in s||"toString"in s||"valueOf"in s)}function ae(s){return!Ab(s)&&!isNaN(parseFloat(s))&&isFinite(s)}function Hb(s,t){const e=Math.round(s);return e-t<=s&&e+t>=s}function G2(s,t,e){let a,i,n;for(a=0,i=s.length;a<i;a++)n=s[a][e],isNaN(n)||(t.min=Math.min(t.min,n),t.max=Math.max(t.max,n))}function ct(s){return s*(O/180)}function ls(s){return s*(180/O)}function Ca(s){if(!N(s))return;let t=1,e=0;for(;Math.round(s*t)/t!==s;)t*=10,e++;return e}function X2(s,t){const e=t.x-s.x,a=t.y-s.y,i=Math.sqrt(e*e+a*a);let n=Math.atan2(a,e);return n<-.5*O&&(n+=I),{angle:n,distance:i}}function q1(s,t){return Math.sqrt(Math.pow(t.x-s.x,2)+Math.pow(t.y-s.y,2))}function Vb(s,t){return(s-t+Cb)%I-O}function Q(s){return(s%I+I)%I}function Be(s,t,e,a){const i=Q(s),n=Q(t),r=Q(e),h=Q(n-i),c=Q(r-i),l=Q(i-n),d=Q(i-r);return i===n||i===r||a&&n===r||h>c&&l<d}function X(s,t,e){return Math.max(t,Math.min(e,s))}function Pb(s){return X(s,-32768,32767)}function wt(s,t,e,a=1e-6){return s>=Math.min(t,e)-a&&s<=Math.max(t,e)+a}function ds(s,t,e){e=e||(r=>s[r]<t);let a=s.length-1,i=0,n;for(;a-i>1;)n=i+a>>1,e(n)?i=n:a=n;return{lo:i,hi:a}}const _t=(s,t,e,a)=>ds(s,e,a?i=>{const n=s[i][t];return n<e||n===e&&s[i+1][t]===e}:i=>s[i][t]<e),Db=(s,t,e)=>ds(s,e,a=>s[a][t]>=e);function Fb(s,t,e){let a=0,i=s.length;for(;a<i&&s[a]<t;)a++;for(;i>a&&s[i-1]>e;)i--;return a>0||i<s.length?s.slice(a,i):s}const Y2=["push","pop","shift","splice","unshift"];function Tb(s,t){if(s._chartjs){s._chartjs.listeners.push(t);return}Object.defineProperty(s,"_chartjs",{configurable:!0,enumerable:!1,value:{listeners:[t]}}),Y2.forEach(e=>{const a="_onData"+cs(e),i=s[e];Object.defineProperty(s,e,{configurable:!0,enumerable:!1,value(...n){const r=i.apply(this,n);return s._chartjs.listeners.forEach(h=>{typeof h[a]=="function"&&h[a](...n)}),r}})})}function Sa(s,t){const e=s._chartjs;if(!e)return;const a=e.listeners,i=a.indexOf(t);i!==-1&&a.splice(i,1),!(a.length>0)&&(Y2.forEach(n=>{delete s[n]}),delete s._chartjs)}function K2(s){const t=new Set(s);return t.size===s.length?s:Array.from(t)}const J2=function(){return typeof window>"u"?function(s){return s()}:window.requestAnimationFrame}();function Q2(s,t){let e=[],a=!1;return function(...i){e=i,a||(a=!0,J2.call(window,()=>{a=!1,s.apply(t,e)}))}}function Bb(s,t){let e;return function(...a){return t?(clearTimeout(e),e=setTimeout(s,t,a)):s.apply(this,a),t}}const ps=s=>s==="start"?"left":s==="end"?"right":"center",J=(s,t,e)=>s==="start"?t:s==="end"?e:(t+e)/2,Ob=(s,t,e,a)=>s===(a?"left":"right")?e:s==="center"?(t+e)/2:t;function ti(s,t,e){const a=t.length;let i=0,n=a;if(s._sorted){const{iScale:r,vScale:h,_parsed:c}=s,l=s.dataset&&s.dataset.options?s.dataset.options.spanGaps:null,d=r.axis,{min:p,max:g,minDefined:u,maxDefined:f}=r.getUserBounds();if(u){if(i=Math.min(_t(c,d,p).lo,e?a:_t(t,d,r.getPixelForValue(p)).lo),l){const v=c.slice(0,i+1).reverse().findIndex(x=>!F(x[h.axis]));i-=Math.max(0,v)}i=X(i,0,a-1)}if(f){let v=Math.max(_t(c,r.axis,g,!0).hi+1,e?0:_t(t,d,r.getPixelForValue(g),!0).hi+1);if(l){const x=c.slice(v-1).findIndex(m=>!F(m[h.axis]));v+=Math.max(0,x)}n=X(v,i,a)-i}else n=a-i}return{start:i,count:n}}function ei(s){const{xScale:t,yScale:e,_scaleRanges:a}=s,i={xmin:t.min,xmax:t.max,ymin:e.min,ymax:e.max};if(!a)return s._scaleRanges=i,!0;const n=a.xmin!==t.min||a.xmax!==t.max||a.ymin!==e.min||a.ymax!==e.max;return Object.assign(a,i),n}const qe=s=>s===0||s===1,La=(s,t,e)=>-(Math.pow(2,10*(s-=1))*Math.sin((s-t)*I/e)),Aa=(s,t,e)=>Math.pow(2,-10*s)*Math.sin((s-t)*I/e)+1,Se={linear:s=>s,easeInQuad:s=>s*s,easeOutQuad:s=>-s*(s-2),easeInOutQuad:s=>(s/=.5)<1?.5*s*s:-.5*(--s*(s-2)-1),easeInCubic:s=>s*s*s,easeOutCubic:s=>(s-=1)*s*s+1,easeInOutCubic:s=>(s/=.5)<1?.5*s*s*s:.5*((s-=2)*s*s+2),easeInQuart:s=>s*s*s*s,easeOutQuart:s=>-((s-=1)*s*s*s-1),easeInOutQuart:s=>(s/=.5)<1?.5*s*s*s*s:-.5*((s-=2)*s*s*s-2),easeInQuint:s=>s*s*s*s*s,easeOutQuint:s=>(s-=1)*s*s*s*s+1,easeInOutQuint:s=>(s/=.5)<1?.5*s*s*s*s*s:.5*((s-=2)*s*s*s*s+2),easeInSine:s=>-Math.cos(s*U)+1,easeOutSine:s=>Math.sin(s*U),easeInOutSine:s=>-.5*(Math.cos(O*s)-1),easeInExpo:s=>s===0?0:Math.pow(2,10*(s-1)),easeOutExpo:s=>s===1?1:-Math.pow(2,-10*s)+1,easeInOutExpo:s=>qe(s)?s:s<.5?.5*Math.pow(2,10*(s*2-1)):.5*(-Math.pow(2,-10*(s*2-1))+2),easeInCirc:s=>s>=1?s:-(Math.sqrt(1-s*s)-1),easeOutCirc:s=>Math.sqrt(1-(s-=1)*s),easeInOutCirc:s=>(s/=.5)<1?-.5*(Math.sqrt(1-s*s)-1):.5*(Math.sqrt(1-(s-=2)*s)+1),easeInElastic:s=>qe(s)?s:La(s,.075,.3),easeOutElastic:s=>qe(s)?s:Aa(s,.075,.3),easeInOutElastic(s){return qe(s)?s:s<.5?.5*La(s*2,.1125,.45):.5+.5*Aa(s*2-1,.1125,.45)},easeInBack(s){return s*s*((1.70158+1)*s-1.70158)},easeOutBack(s){return(s-=1)*s*((1.70158+1)*s+1.70158)+1},easeInOutBack(s){let t=1.70158;return(s/=.5)<1?.5*(s*s*(((t*=1.525)+1)*s-t)):.5*((s-=2)*s*(((t*=1.525)+1)*s+t)+2)},easeInBounce:s=>1-Se.easeOutBounce(1-s),easeOutBounce(s){return s<1/2.75?7.5625*s*s:s<2/2.75?7.5625*(s-=1.5/2.75)*s+.75:s<2.5/2.75?7.5625*(s-=2.25/2.75)*s+.9375:7.5625*(s-=2.625/2.75)*s+.984375},easeInOutBounce:s=>s<.5?Se.easeInBounce(s*2)*.5:Se.easeOutBounce(s*2-1)*.5+.5};function gs(s){if(s&&typeof s=="object"){const t=s.toString();return t==="[object CanvasPattern]"||t==="[object CanvasGradient]"}return!1}function Ha(s){return gs(s)?s:new De(s)}function D1(s){return gs(s)?s:new De(s).saturate(.5).darken(.1).hexString()}const Eb=["x","y","borderWidth","radius","tension"],Rb=["color","borderColor","backgroundColor"];function zb(s){s.set("animation",{delay:void 0,duration:1e3,easing:"easeOutQuart",fn:void 0,from:void 0,loop:void 0,to:void 0,type:void 0}),s.describe("animation",{_fallback:!1,_indexable:!1,_scriptable:t=>t!=="onProgress"&&t!=="onComplete"&&t!=="fn"}),s.set("animations",{colors:{type:"color",properties:Rb},numbers:{type:"number",properties:Eb}}),s.describe("animations",{_fallback:"animation"}),s.set("transitions",{active:{animation:{duration:400}},resize:{animation:{duration:0}},show:{animations:{colors:{from:"transparent"},visible:{type:"boolean",duration:0}}},hide:{animations:{colors:{to:"transparent"},visible:{type:"boolean",easing:"linear",fn:t=>t|0}}}})}function Ib(s){s.set("layout",{autoPadding:!0,padding:{top:0,right:0,bottom:0,left:0}})}const Va=new Map;function $b(s,t){t=t||{};const e=s+JSON.stringify(t);let a=Va.get(e);return a||(a=new Intl.NumberFormat(s,t),Va.set(e,a)),a}function $e(s,t,e){return $b(t,e).format(s)}const si={values(s){return Z(s)?s:""+s},numeric(s,t,e){if(s===0)return"0";const a=this.chart.options.locale;let i,n=s;if(e.length>1){const l=Math.max(Math.abs(e[0].value),Math.abs(e[e.length-1].value));(l<1e-4||l>1e15)&&(i="scientific"),n=Zb(s,e)}const r=Lt(Math.abs(n)),h=isNaN(r)?1:Math.max(Math.min(-1*Math.floor(r),20),0),c={notation:i,minimumFractionDigits:h,maximumFractionDigits:h};return Object.assign(c,this.options.ticks.format),$e(s,a,c)},logarithmic(s,t,e){if(s===0)return"0";const a=e[t].significand||s/Math.pow(10,Math.floor(Lt(s)));return[1,2,3,5,10,15].includes(a)||t>.8*e.length?si.numeric.call(this,s,t,e):""}};function Zb(s,t){let e=t.length>3?t[2].value-t[1].value:t[1].value-t[0].value;return Math.abs(e)>=1&&s!==Math.floor(s)&&(e=s-Math.floor(s)),e}var w1={formatters:si};function Wb(s){s.set("scale",{display:!0,offset:!1,reverse:!1,beginAtZero:!1,bounds:"ticks",clip:!0,grace:0,grid:{display:!0,lineWidth:1,drawOnChartArea:!0,drawTicks:!0,tickLength:8,tickWidth:(t,e)=>e.lineWidth,tickColor:(t,e)=>e.color,offset:!1},border:{display:!0,dash:[],dashOffset:0,width:1},title:{display:!1,text:"",padding:{top:4,bottom:4}},ticks:{minRotation:0,maxRotation:50,mirror:!1,textStrokeWidth:0,textStrokeColor:"",padding:3,display:!0,autoSkip:!0,autoSkipPadding:3,labelOffset:0,callback:w1.formatters.values,minor:{},major:{},align:"center",crossAlign:"near",showLabelBackdrop:!1,backdropColor:"rgba(255, 255, 255, 0.75)",backdropPadding:2}}),s.route("scale.ticks","color","","color"),s.route("scale.grid","color","","borderColor"),s.route("scale.border","color","","borderColor"),s.route("scale.title","color","","color"),s.describe("scale",{_fallback:!1,_scriptable:t=>!t.startsWith("before")&&!t.startsWith("after")&&t!=="callback"&&t!=="parser",_indexable:t=>t!=="borderDash"&&t!=="tickBorderDash"&&t!=="dash"}),s.describe("scales",{_fallback:"scale"}),s.describe("scale.ticks",{_scriptable:t=>t!=="backdropPadding"&&t!=="callback",_indexable:t=>t!=="backdropPadding"})}const Gt=Object.create(null),G1=Object.create(null);function Le(s,t){if(!t)return s;const e=t.split(".");for(let a=0,i=e.length;a<i;++a){const n=e[a];s=s[n]||(s[n]=Object.create(null))}return s}function F1(s,t,e){return typeof t=="string"?Fe(Le(s,t),e):Fe(Le(s,""),t)}class Nb{constructor(t,e){this.animation=void 0,this.backgroundColor="rgba(0,0,0,0.1)",this.borderColor="rgba(0,0,0,0.1)",this.color="#666",this.datasets={},this.devicePixelRatio=a=>a.chart.platform.getDevicePixelRatio(),this.elements={},this.events=["mousemove","mouseout","click","touchstart","touchmove"],this.font={family:"'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",size:12,style:"normal",lineHeight:1.2,weight:null},this.hover={},this.hoverBackgroundColor=(a,i)=>D1(i.backgroundColor),this.hoverBorderColor=(a,i)=>D1(i.borderColor),this.hoverColor=(a,i)=>D1(i.color),this.indexAxis="x",this.interaction={mode:"nearest",intersect:!0,includeInvisible:!1},this.maintainAspectRatio=!0,this.onHover=null,this.onClick=null,this.parsing=!0,this.plugins={},this.responsive=!0,this.scale=void 0,this.scales={},this.showLine=!0,this.drawActiveElementsOnTop=!0,this.describe(t),this.apply(e)}set(t,e){return F1(this,t,e)}get(t){return Le(this,t)}describe(t,e){return F1(G1,t,e)}override(t,e){return F1(Gt,t,e)}route(t,e,a,i){const n=Le(this,t),r=Le(this,a),h="_"+e;Object.defineProperties(n,{[h]:{value:n[e],writable:!0},[e]:{enumerable:!0,get(){const c=this[h],l=r[i];return T(c)?Object.assign({},l,c):H(c,l)},set(c){this[h]=c}}})}apply(t){t.forEach(e=>e(this))}}var W=new Nb({_scriptable:s=>!s.startsWith("on"),_indexable:s=>s!=="events",hover:{_fallback:"interaction"},interaction:{_scriptable:!1,_indexable:!1}},[zb,Ib,Wb]);function jb(s){return!s||F(s.size)||F(s.family)?null:(s.style?s.style+" ":"")+(s.weight?s.weight+" ":"")+s.size+"px "+s.family}function f1(s,t,e,a,i){let n=t[i];return n||(n=t[i]=s.measureText(i).width,e.push(i)),n>a&&(a=n),a}function Ub(s,t,e,a){a=a||{};let i=a.data=a.data||{},n=a.garbageCollect=a.garbageCollect||[];a.font!==t&&(i=a.data={},n=a.garbageCollect=[],a.font=t),s.save(),s.font=t;let r=0;const h=e.length;let c,l,d,p,g;for(c=0;c<h;c++)if(p=e[c],p!=null&&!Z(p))r=f1(s,i,n,r,p);else if(Z(p))for(l=0,d=p.length;l<d;l++)g=p[l],g!=null&&!Z(g)&&(r=f1(s,i,n,r,g));s.restore();const u=n.length/2;if(u>e.length){for(c=0;c<u;c++)delete i[n[c]];n.splice(0,u)}return r}function Et(s,t,e){const a=s.currentDevicePixelRatio,i=e!==0?Math.max(e/2,.5):0;return Math.round((t-i)*a)/a+i}function Pa(s,t){!t&&!s||(t=t||s.getContext("2d"),t.save(),t.resetTransform(),t.clearRect(0,0,s.width,s.height),t.restore())}function X1(s,t,e,a){ai(s,t,e,a,null)}function ai(s,t,e,a,i){let n,r,h,c,l,d,p,g;const u=t.pointStyle,f=t.rotation,v=t.radius;let x=(f||0)*Sb;if(u&&typeof u=="object"&&(n=u.toString(),n==="[object HTMLImageElement]"||n==="[object HTMLCanvasElement]")){s.save(),s.translate(e,a),s.rotate(x),s.drawImage(u,-u.width/2,-u.height/2,u.width,u.height),s.restore();return}if(!(isNaN(v)||v<=0)){switch(s.beginPath(),u){default:i?s.ellipse(e,a,i/2,v,0,0,I):s.arc(e,a,v,0,I),s.closePath();break;case"triangle":d=i?i/2:v,s.moveTo(e+Math.sin(x)*d,a-Math.cos(x)*v),x+=_a,s.lineTo(e+Math.sin(x)*d,a-Math.cos(x)*v),x+=_a,s.lineTo(e+Math.sin(x)*d,a-Math.cos(x)*v),s.closePath();break;case"rectRounded":l=v*.516,c=v-l,r=Math.cos(x+Ot)*c,p=Math.cos(x+Ot)*(i?i/2-l:c),h=Math.sin(x+Ot)*c,g=Math.sin(x+Ot)*(i?i/2-l:c),s.arc(e-p,a-h,l,x-O,x-U),s.arc(e+g,a-r,l,x-U,x),s.arc(e+p,a+h,l,x,x+U),s.arc(e-g,a+r,l,x+U,x+O),s.closePath();break;case"rect":if(!f){c=Math.SQRT1_2*v,d=i?i/2:c,s.rect(e-d,a-c,2*d,2*c);break}x+=Ot;case"rectRot":p=Math.cos(x)*(i?i/2:v),r=Math.cos(x)*v,h=Math.sin(x)*v,g=Math.sin(x)*(i?i/2:v),s.moveTo(e-p,a-h),s.lineTo(e+g,a-r),s.lineTo(e+p,a+h),s.lineTo(e-g,a+r),s.closePath();break;case"crossRot":x+=Ot;case"cross":p=Math.cos(x)*(i?i/2:v),r=Math.cos(x)*v,h=Math.sin(x)*v,g=Math.sin(x)*(i?i/2:v),s.moveTo(e-p,a-h),s.lineTo(e+p,a+h),s.moveTo(e+g,a-r),s.lineTo(e-g,a+r);break;case"star":p=Math.cos(x)*(i?i/2:v),r=Math.cos(x)*v,h=Math.sin(x)*v,g=Math.sin(x)*(i?i/2:v),s.moveTo(e-p,a-h),s.lineTo(e+p,a+h),s.moveTo(e+g,a-r),s.lineTo(e-g,a+r),x+=Ot,p=Math.cos(x)*(i?i/2:v),r=Math.cos(x)*v,h=Math.sin(x)*v,g=Math.sin(x)*(i?i/2:v),s.moveTo(e-p,a-h),s.lineTo(e+p,a+h),s.moveTo(e+g,a-r),s.lineTo(e-g,a+r);break;case"line":r=i?i/2:Math.cos(x)*v,h=Math.sin(x)*v,s.moveTo(e-r,a-h),s.lineTo(e+r,a+h);break;case"dash":s.moveTo(e,a),s.lineTo(e+Math.cos(x)*(i?i/2:v),a+Math.sin(x)*v);break;case!1:s.closePath();break}s.fill(),t.borderWidth>0&&s.stroke()}}function kt(s,t,e){return e=e||.5,!t||s&&s.x>t.left-e&&s.x<t.right+e&&s.y>t.top-e&&s.y<t.bottom+e}function _1(s,t){s.save(),s.beginPath(),s.rect(t.left,t.top,t.right-t.left,t.bottom-t.top),s.clip()}function k1(s){s.restore()}function qb(s,t,e,a,i){if(!t)return s.lineTo(e.x,e.y);if(i==="middle"){const n=(t.x+e.x)/2;s.lineTo(n,t.y),s.lineTo(n,e.y)}else i==="after"!=!!a?s.lineTo(t.x,e.y):s.lineTo(e.x,t.y);s.lineTo(e.x,e.y)}function Gb(s,t,e,a){if(!t)return s.lineTo(e.x,e.y);s.bezierCurveTo(a?t.cp1x:t.cp2x,a?t.cp1y:t.cp2y,a?e.cp2x:e.cp1x,a?e.cp2y:e.cp1y,e.x,e.y)}function Xb(s,t){t.translation&&s.translate(t.translation[0],t.translation[1]),F(t.rotation)||s.rotate(t.rotation),t.color&&(s.fillStyle=t.color),t.textAlign&&(s.textAlign=t.textAlign),t.textBaseline&&(s.textBaseline=t.textBaseline)}function Yb(s,t,e,a,i){if(i.strikethrough||i.underline){const n=s.measureText(a),r=t-n.actualBoundingBoxLeft,h=t+n.actualBoundingBoxRight,c=e-n.actualBoundingBoxAscent,l=e+n.actualBoundingBoxDescent,d=i.strikethrough?(c+l)/2:l;s.strokeStyle=s.fillStyle,s.beginPath(),s.lineWidth=i.decorationWidth||2,s.moveTo(r,d),s.lineTo(h,d),s.stroke()}}function Kb(s,t){const e=s.fillStyle;s.fillStyle=t.color,s.fillRect(t.left,t.top,t.width,t.height),s.fillStyle=e}function Xt(s,t,e,a,i,n={}){const r=Z(t)?t:[t],h=n.strokeWidth>0&&n.strokeColor!=="";let c,l;for(s.save(),s.font=i.string,Xb(s,n),c=0;c<r.length;++c)l=r[c],n.backdrop&&Kb(s,n.backdrop),h&&(n.strokeColor&&(s.strokeStyle=n.strokeColor),F(n.strokeWidth)||(s.lineWidth=n.strokeWidth),s.strokeText(l,e,a,n.maxWidth)),s.fillText(l,e,a,n.maxWidth),Yb(s,e,a,l,n),a+=Number(i.lineHeight);s.restore()}function Oe(s,t){const{x:e,y:a,w:i,h:n,radius:r}=t;s.arc(e+r.topLeft,a+r.topLeft,r.topLeft,1.5*O,O,!0),s.lineTo(e,a+n-r.bottomLeft),s.arc(e+r.bottomLeft,a+n-r.bottomLeft,r.bottomLeft,O,U,!0),s.lineTo(e+i-r.bottomRight,a+n),s.arc(e+i-r.bottomRight,a+n-r.bottomRight,r.bottomRight,U,0,!0),s.lineTo(e+i,a+r.topRight),s.arc(e+i-r.topRight,a+r.topRight,r.topRight,0,-U,!0),s.lineTo(e+r.topLeft,a)}const Jb=/^(normal|(\d+(?:\.\d+)?)(px|em|%)?)$/,Qb=/^(normal|italic|initial|inherit|unset|(oblique( -?[0-9]?[0-9]deg)?))$/;function tw(s,t){const e=(""+s).match(Jb);if(!e||e[1]==="normal")return t*1.2;switch(s=+e[2],e[3]){case"px":return s;case"%":s/=100;break}return t*s}const ew=s=>+s||0;function us(s,t){const e={},a=T(t),i=a?Object.keys(t):t,n=T(s)?a?r=>H(s[r],s[t[r]]):r=>s[r]:()=>s;for(const r of i)e[r]=ew(n(r));return e}function ii(s){return us(s,{top:"y",right:"x",bottom:"y",left:"x"})}function jt(s){return us(s,["topLeft","topRight","bottomLeft","bottomRight"])}function et(s){const t=ii(s);return t.width=t.left+t.right,t.height=t.top+t.bottom,t}function G(s,t){s=s||{},t=t||W.font;let e=H(s.size,t.size);typeof e=="string"&&(e=parseInt(e,10));let a=H(s.style,t.style);a&&!(""+a).match(Qb)&&(console.warn('Invalid font style specified: "'+a+'"'),a=void 0);const i={family:H(s.family,t.family),lineHeight:tw(H(s.lineHeight,t.lineHeight),e),size:e,style:a,weight:H(s.weight,t.weight),string:""};return i.string=jb(i),i}function me(s,t,e,a){let i,n,r;for(i=0,n=s.length;i<n;++i)if(r=s[i],r!==void 0&&r!==void 0)return r}function sw(s,t,e){const{min:a,max:i}=s,n=U2(t,(i-a)/2),r=(h,c)=>e&&h===0?0:h+c;return{min:r(a,-Math.abs(n)),max:r(i,n)}}function Ft(s,t){return Object.assign(Object.create(s),t)}function fs(s,t=[""],e,a,i=()=>s[0]){const n=e||s;typeof a>"u"&&(a=hi("_fallback",s));const r={[Symbol.toStringTag]:"Object",_cacheable:!0,_scopes:s,_rootScopes:n,_fallback:a,_getTarget:i,override:h=>fs([h,...s],t,n,a)};return new Proxy(r,{deleteProperty(h,c){return delete h[c],delete h._keys,delete s[0][c],!0},get(h,c){return oi(h,c,()=>lw(c,t,s,h))},getOwnPropertyDescriptor(h,c){return Reflect.getOwnPropertyDescriptor(h._scopes[0],c)},getPrototypeOf(){return Reflect.getPrototypeOf(s[0])},has(h,c){return Fa(h).includes(c)},ownKeys(h){return Fa(h)},set(h,c,l){const d=h._storage||(h._storage=i());return h[c]=d[c]=l,delete h._keys,!0}})}function ie(s,t,e,a){const i={_cacheable:!1,_proxy:s,_context:t,_subProxy:e,_stack:new Set,_descriptors:ni(s,a),setContext:n=>ie(s,n,e,a),override:n=>ie(s.override(n),t,e,a)};return new Proxy(i,{deleteProperty(n,r){return delete n[r],delete s[r],!0},get(n,r,h){return oi(n,r,()=>iw(n,r,h))},getOwnPropertyDescriptor(n,r){return n._descriptors.allKeys?Reflect.has(s,r)?{enumerable:!0,configurable:!0}:void 0:Reflect.getOwnPropertyDescriptor(s,r)},getPrototypeOf(){return Reflect.getPrototypeOf(s)},has(n,r){return Reflect.has(s,r)},ownKeys(){return Reflect.ownKeys(s)},set(n,r,h){return s[r]=h,delete n[r],!0}})}function ni(s,t={scriptable:!0,indexable:!0}){const{_scriptable:e=t.scriptable,_indexable:a=t.indexable,_allKeys:i=t.allKeys}=s;return{allKeys:i,scriptable:e,indexable:a,isScriptable:Dt(e)?e:()=>e,isIndexable:Dt(a)?a:()=>a}}const aw=(s,t)=>s?s+cs(t):t,vs=(s,t)=>T(t)&&s!=="adapters"&&(Object.getPrototypeOf(t)===null||t.constructor===Object);function oi(s,t,e){if(Object.prototype.hasOwnProperty.call(s,t)||t==="constructor")return s[t];const a=e();return s[t]=a,a}function iw(s,t,e){const{_proxy:a,_context:i,_subProxy:n,_descriptors:r}=s;let h=a[t];return Dt(h)&&r.isScriptable(t)&&(h=nw(t,h,s,e)),Z(h)&&h.length&&(h=ow(t,h,s,r.isIndexable)),vs(t,h)&&(h=ie(h,i,n&&n[t],r)),h}function nw(s,t,e,a){const{_proxy:i,_context:n,_subProxy:r,_stack:h}=e;if(h.has(s))throw new Error("Recursion detected: "+Array.from(h).join("->")+"->"+s);h.add(s);let c=t(n,r||a);return h.delete(s),vs(s,c)&&(c=xs(i._scopes,i,s,c)),c}function ow(s,t,e,a){const{_proxy:i,_context:n,_subProxy:r,_descriptors:h}=e;if(typeof n.index<"u"&&a(s))return t[n.index%t.length];if(T(t[0])){const c=t,l=i._scopes.filter(d=>d!==c);t=[];for(const d of c){const p=xs(l,i,s,d);t.push(ie(p,n,r&&r[s],h))}}return t}function ri(s,t,e){return Dt(s)?s(t,e):s}const rw=(s,t)=>s===!0?t:typeof s=="string"?Pt(t,s):void 0;function hw(s,t,e,a,i){for(const n of t){const r=rw(e,n);if(r){s.add(r);const h=ri(r._fallback,e,i);if(typeof h<"u"&&h!==e&&h!==a)return h}else if(r===!1&&typeof a<"u"&&e!==a)return null}return!1}function xs(s,t,e,a){const i=t._rootScopes,n=ri(t._fallback,e,a),r=[...s,...i],h=new Set;h.add(a);let c=Da(h,r,e,n||e,a);return c===null||typeof n<"u"&&n!==e&&(c=Da(h,r,n,c,a),c===null)?!1:fs(Array.from(h),[""],i,n,()=>cw(t,e,a))}function Da(s,t,e,a,i){for(;e;)e=hw(s,t,e,a,i);return e}function cw(s,t,e){const a=s._getTarget();t in a||(a[t]={});const i=a[t];return Z(i)&&T(e)?e:i||{}}function lw(s,t,e,a){let i;for(const n of t)if(i=hi(aw(n,s),e),typeof i<"u")return vs(s,i)?xs(e,a,s,i):i}function hi(s,t){for(const e of t){if(!e)continue;const a=e[s];if(typeof a<"u")return a}}function Fa(s){let t=s._keys;return t||(t=s._keys=dw(s._scopes)),t}function dw(s){const t=new Set;for(const e of s)for(const a of Object.keys(e).filter(i=>!i.startsWith("_")))t.add(a);return Array.from(t)}function ci(s,t,e,a){const{iScale:i}=s,{key:n="r"}=this._parsing,r=new Array(a);let h,c,l,d;for(h=0,c=a;h<c;++h)l=h+e,d=t[l],r[h]={r:i.parse(Pt(d,n),l)};return r}const pw=Number.EPSILON||1e-14,ne=(s,t)=>t<s.length&&!s[t].skip&&s[t],li=s=>s==="x"?"y":"x";function gw(s,t,e,a){const i=s.skip?t:s,n=t,r=e.skip?t:e,h=q1(n,i),c=q1(r,n);let l=h/(h+c),d=c/(h+c);l=isNaN(l)?0:l,d=isNaN(d)?0:d;const p=a*l,g=a*d;return{previous:{x:n.x-p*(r.x-i.x),y:n.y-p*(r.y-i.y)},next:{x:n.x+g*(r.x-i.x),y:n.y+g*(r.y-i.y)}}}function uw(s,t,e){const a=s.length;let i,n,r,h,c,l=ne(s,0);for(let d=0;d<a-1;++d)if(c=l,l=ne(s,d+1),!(!c||!l)){if(Ce(t[d],0,pw)){e[d]=e[d+1]=0;continue}i=e[d]/t[d],n=e[d+1]/t[d],h=Math.pow(i,2)+Math.pow(n,2),!(h<=9)&&(r=3/Math.sqrt(h),e[d]=i*r*t[d],e[d+1]=n*r*t[d])}}function fw(s,t,e="x"){const a=li(e),i=s.length;let n,r,h,c=ne(s,0);for(let l=0;l<i;++l){if(r=h,h=c,c=ne(s,l+1),!h)continue;const d=h[e],p=h[a];r&&(n=(d-r[e])/3,h[`cp1${e}`]=d-n,h[`cp1${a}`]=p-n*t[l]),c&&(n=(c[e]-d)/3,h[`cp2${e}`]=d+n,h[`cp2${a}`]=p+n*t[l])}}function vw(s,t="x"){const e=li(t),a=s.length,i=Array(a).fill(0),n=Array(a);let r,h,c,l=ne(s,0);for(r=0;r<a;++r)if(h=c,c=l,l=ne(s,r+1),!!c){if(l){const d=l[t]-c[t];i[r]=d!==0?(l[e]-c[e])/d:0}n[r]=h?l?xt(i[r-1])!==xt(i[r])?0:(i[r-1]+i[r])/2:i[r-1]:i[r]}uw(s,i,n),fw(s,n,t)}function Ge(s,t,e){return Math.max(Math.min(s,e),t)}function xw(s,t){let e,a,i,n,r,h=kt(s[0],t);for(e=0,a=s.length;e<a;++e)r=n,n=h,h=e<a-1&&kt(s[e+1],t),n&&(i=s[e],r&&(i.cp1x=Ge(i.cp1x,t.left,t.right),i.cp1y=Ge(i.cp1y,t.top,t.bottom)),h&&(i.cp2x=Ge(i.cp2x,t.left,t.right),i.cp2y=Ge(i.cp2y,t.top,t.bottom)))}function mw(s,t,e,a,i){let n,r,h,c;if(t.spanGaps&&(s=s.filter(l=>!l.skip)),t.cubicInterpolationMode==="monotone")vw(s,i);else{let l=a?s[s.length-1]:s[0];for(n=0,r=s.length;n<r;++n)h=s[n],c=gw(l,h,s[Math.min(n+1,r-(a?0:1))%r],t.tension),h.cp1x=c.previous.x,h.cp1y=c.previous.y,h.cp2x=c.next.x,h.cp2y=c.next.y,l=h}t.capBezierPoints&&xw(s,e)}function ms(){return typeof window<"u"&&typeof document<"u"}function Ms(s){let t=s.parentNode;return t&&t.toString()==="[object ShadowRoot]"&&(t=t.host),t}function v1(s,t,e){let a;return typeof s=="string"?(a=parseInt(s,10),s.indexOf("%")!==-1&&(a=a/100*t.parentNode[e])):a=s,a}const C1=s=>s.ownerDocument.defaultView.getComputedStyle(s,null);function Mw(s,t){return C1(s).getPropertyValue(t)}const yw=["top","right","bottom","left"];function Ut(s,t,e){const a={};e=e?"-"+e:"";for(let i=0;i<4;i++){const n=yw[i];a[n]=parseFloat(s[t+"-"+n+e])||0}return a.width=a.left+a.right,a.height=a.top+a.bottom,a}const bw=(s,t,e)=>(s>0||t>0)&&(!e||!e.shadowRoot);function ww(s,t){const e=s.touches,a=e&&e.length?e[0]:s,{offsetX:i,offsetY:n}=a;let r=!1,h,c;if(bw(i,n,s.target))h=i,c=n;else{const l=t.getBoundingClientRect();h=a.clientX-l.left,c=a.clientY-l.top,r=!0}return{x:h,y:c,box:r}}function It(s,t){if("native"in s)return s;const{canvas:e,currentDevicePixelRatio:a}=t,i=C1(e),n=i.boxSizing==="border-box",r=Ut(i,"padding"),h=Ut(i,"border","width"),{x:c,y:l,box:d}=ww(s,e),p=r.left+(d&&h.left),g=r.top+(d&&h.top);let{width:u,height:f}=t;return n&&(u-=r.width+h.width,f-=r.height+h.height),{x:Math.round((c-p)/u*e.width/a),y:Math.round((l-g)/f*e.height/a)}}function _w(s,t,e){let a,i;if(t===void 0||e===void 0){const n=s&&Ms(s);if(!n)t=s.clientWidth,e=s.clientHeight;else{const r=n.getBoundingClientRect(),h=C1(n),c=Ut(h,"border","width"),l=Ut(h,"padding");t=r.width-l.width-c.width,e=r.height-l.height-c.height,a=v1(h.maxWidth,n,"clientWidth"),i=v1(h.maxHeight,n,"clientHeight")}}return{width:t,height:e,maxWidth:a||u1,maxHeight:i||u1}}const At=s=>Math.round(s*10)/10;function kw(s,t,e,a){const i=C1(s),n=Ut(i,"margin"),r=v1(i.maxWidth,s,"clientWidth")||u1,h=v1(i.maxHeight,s,"clientHeight")||u1,c=_w(s,t,e);let{width:l,height:d}=c;if(i.boxSizing==="content-box"){const g=Ut(i,"border","width"),u=Ut(i,"padding");l-=u.width+g.width,d-=u.height+g.height}return l=Math.max(0,l-n.width),d=Math.max(0,a?l/a:d-n.height),l=At(Math.min(l,r,c.maxWidth)),d=At(Math.min(d,h,c.maxHeight)),l&&!d&&(d=At(l/2)),(t!==void 0||e!==void 0)&&a&&c.height&&d>c.height&&(d=c.height,l=At(Math.floor(d*a))),{width:l,height:d}}function Ta(s,t,e){const a=t||1,i=At(s.height*a),n=At(s.width*a);s.height=At(s.height),s.width=At(s.width);const r=s.canvas;return r.style&&(e||!r.style.height&&!r.style.width)&&(r.style.height=`${s.height}px`,r.style.width=`${s.width}px`),s.currentDevicePixelRatio!==a||r.height!==i||r.width!==n?(s.currentDevicePixelRatio=a,r.height=i,r.width=n,s.ctx.setTransform(a,0,0,a,0,0),!0):!1}const Cw=function(){let s=!1;try{const t={get passive(){return s=!0,!1}};ms()&&(window.addEventListener("test",null,t),window.removeEventListener("test",null,t))}catch{}return s}();function Ba(s,t){const e=Mw(s,t),a=e&&e.match(/^(\d+)(\.\d+)?px$/);return a?+a[1]:void 0}function $t(s,t,e,a){return{x:s.x+e*(t.x-s.x),y:s.y+e*(t.y-s.y)}}function Sw(s,t,e,a){return{x:s.x+e*(t.x-s.x),y:a==="middle"?e<.5?s.y:t.y:a==="after"?e<1?s.y:t.y:e>0?t.y:s.y}}function Lw(s,t,e,a){const i={x:s.cp2x,y:s.cp2y},n={x:t.cp1x,y:t.cp1y},r=$t(s,i,e),h=$t(i,n,e),c=$t(n,t,e),l=$t(r,h,e),d=$t(h,c,e);return $t(l,d,e)}const Aw=function(s,t){return{x(e){return s+s+t-e},setWidth(e){t=e},textAlign(e){return e==="center"?e:e==="right"?"left":"right"},xPlus(e,a){return e-a},leftForLtr(e,a){return e-a}}},Hw=function(){return{x(s){return s},setWidth(s){},textAlign(s){return s},xPlus(s,t){return s+t},leftForLtr(s,t){return s}}};function se(s,t,e){return s?Aw(t,e):Hw()}function di(s,t){let e,a;(t==="ltr"||t==="rtl")&&(e=s.canvas.style,a=[e.getPropertyValue("direction"),e.getPropertyPriority("direction")],e.setProperty("direction",t,"important"),s.prevTextDirection=a)}function pi(s,t){t!==void 0&&(delete s.prevTextDirection,s.canvas.style.setProperty("direction",t[0],t[1]))}function gi(s){return s==="angle"?{between:Be,compare:Vb,normalize:Q}:{between:wt,compare:(t,e)=>t-e,normalize:t=>t}}function Oa({start:s,end:t,count:e,loop:a,style:i}){return{start:s%e,end:t%e,loop:a&&(t-s+1)%e===0,style:i}}function Vw(s,t,e){const{property:a,start:i,end:n}=e,{between:r,normalize:h}=gi(a),c=t.length;let{start:l,end:d,loop:p}=s,g,u;if(p){for(l+=c,d+=c,g=0,u=c;g<u&&r(h(t[l%c][a]),i,n);++g)l--,d--;l%=c,d%=c}return d<l&&(d+=c),{start:l,end:d,loop:p,style:s.style}}function ui(s,t,e){if(!e)return[s];const{property:a,start:i,end:n}=e,r=t.length,{compare:h,between:c,normalize:l}=gi(a),{start:d,end:p,loop:g,style:u}=Vw(s,t,e),f=[];let v=!1,x=null,m,M,b;const w=()=>c(i,b,m)&&h(i,b)!==0,y=()=>h(n,m)===0||c(n,b,m),k=()=>v||w(),C=()=>!v||y();for(let S=d,L=d;S<=p;++S)M=t[S%r],!M.skip&&(m=l(M[a]),m!==b&&(v=c(m,i,n),x===null&&k()&&(x=h(m,i)===0?S:L),x!==null&&C()&&(f.push(Oa({start:x,end:S,loop:g,count:r,style:u})),x=null),L=S,b=m));return x!==null&&f.push(Oa({start:x,end:p,loop:g,count:r,style:u})),f}function fi(s,t){const e=[],a=s.segments;for(let i=0;i<a.length;i++){const n=ui(a[i],s.points,t);n.length&&e.push(...n)}return e}function Pw(s,t,e,a){let i=0,n=t-1;if(e&&!a)for(;i<t&&!s[i].skip;)i++;for(;i<t&&s[i].skip;)i++;for(i%=t,e&&(n+=i);n>i&&s[n%t].skip;)n--;return n%=t,{start:i,end:n}}function Dw(s,t,e,a){const i=s.length,n=[];let r=t,h=s[t],c;for(c=t+1;c<=e;++c){const l=s[c%i];l.skip||l.stop?h.skip||(a=!1,n.push({start:t%i,end:(c-1)%i,loop:a}),t=r=l.stop?c:null):(r=c,h.skip&&(t=c)),h=l}return r!==null&&n.push({start:t%i,end:r%i,loop:a}),n}function Fw(s,t){const e=s.points,a=s.options.spanGaps,i=e.length;if(!i)return[];const n=!!s._loop,{start:r,end:h}=Pw(e,i,n,a);if(a===!0)return Ea(s,[{start:r,end:h,loop:n}],e,t);const c=h<r?h+i:h,l=!!s._fullLoop&&r===0&&h===i-1;return Ea(s,Dw(e,r,c,l),e,t)}function Ea(s,t,e,a){return!a||!a.setContext||!e?t:Tw(s,t,e,a)}function Tw(s,t,e,a){const i=s._chart.getContext(),n=Ra(s.options),{_datasetIndex:r,options:{spanGaps:h}}=s,c=e.length,l=[];let d=n,p=t[0].start,g=p;function u(f,v,x,m){const M=h?-1:1;if(f!==v){for(f+=c;e[f%c].skip;)f-=M;for(;e[v%c].skip;)v+=M;f%c!==v%c&&(l.push({start:f%c,end:v%c,loop:x,style:m}),d=m,p=v%c)}}for(const f of t){p=h?p:f.start;let v=e[p%c],x;for(g=p+1;g<=f.end;g++){const m=e[g%c];x=Ra(a.setContext(Ft(i,{type:"segment",p0:v,p1:m,p0DataIndex:(g-1)%c,p1DataIndex:g%c,datasetIndex:r}))),Bw(x,d)&&u(p,g-1,f.loop,d),v=m,d=x}p<g-1&&u(p,g-1,f.loop,d)}return l}function Ra(s){return{backgroundColor:s.backgroundColor,borderCapStyle:s.borderCapStyle,borderDash:s.borderDash,borderDashOffset:s.borderDashOffset,borderJoinStyle:s.borderJoinStyle,borderWidth:s.borderWidth,borderColor:s.borderColor}}function Bw(s,t){if(!t)return!1;const e=[],a=function(i,n){return gs(n)?(e.includes(n)||e.push(n),e.indexOf(n)):n};return JSON.stringify(s,a)!==JSON.stringify(t,a)}function Xe(s,t,e){return s.options.clip?s[e]:t[e]}function Ow(s,t){const{xScale:e,yScale:a}=s;return e&&a?{left:Xe(e,t,"left"),right:Xe(e,t,"right"),top:Xe(a,t,"top"),bottom:Xe(a,t,"bottom")}:t}function vi(s,t){const e=t._clip;if(e.disabled)return!1;const a=Ow(t,s.chartArea);return{left:e.left===!1?0:a.left-(e.left===!0?0:e.left),right:e.right===!1?s.width:a.right+(e.right===!0?0:e.right),top:e.top===!1?0:a.top-(e.top===!0?0:e.top),bottom:e.bottom===!1?s.height:a.bottom+(e.bottom===!0?0:e.bottom)}}/*!
 * Chart.js v4.5.1
 * https://www.chartjs.org
 * (c) 2025 Chart.js Contributors
 * Released under the MIT License
 */class Ew{constructor(){this._request=null,this._charts=new Map,this._running=!1,this._lastDate=void 0}_notify(t,e,a,i){const n=e.listeners[i],r=e.duration;n.forEach(h=>h({chart:t,initial:e.initial,numSteps:r,currentStep:Math.min(a-e.start,r)}))}_refresh(){this._request||(this._running=!0,this._request=J2.call(window,()=>{this._update(),this._request=null,this._running&&this._refresh()}))}_update(t=Date.now()){let e=0;this._charts.forEach((a,i)=>{if(!a.running||!a.items.length)return;const n=a.items;let r=n.length-1,h=!1,c;for(;r>=0;--r)c=n[r],c._active?(c._total>a.duration&&(a.duration=c._total),c.tick(t),h=!0):(n[r]=n[n.length-1],n.pop());h&&(i.draw(),this._notify(i,a,t,"progress")),n.length||(a.running=!1,this._notify(i,a,t,"complete"),a.initial=!1),e+=n.length}),this._lastDate=t,e===0&&(this._running=!1)}_getAnims(t){const e=this._charts;let a=e.get(t);return a||(a={running:!1,initial:!0,items:[],listeners:{complete:[],progress:[]}},e.set(t,a)),a}listen(t,e,a){this._getAnims(t).listeners[e].push(a)}add(t,e){!e||!e.length||this._getAnims(t).items.push(...e)}has(t){return this._getAnims(t).items.length>0}start(t){const e=this._charts.get(t);e&&(e.running=!0,e.start=Date.now(),e.duration=e.items.reduce((a,i)=>Math.max(a,i._duration),0),this._refresh())}running(t){if(!this._running)return!1;const e=this._charts.get(t);return!(!e||!e.running||!e.items.length)}stop(t){const e=this._charts.get(t);if(!e||!e.items.length)return;const a=e.items;let i=a.length-1;for(;i>=0;--i)a[i].cancel();e.items=[],this._notify(t,e,Date.now(),"complete")}remove(t){return this._charts.delete(t)}}var Mt=new Ew;const za="transparent",Rw={boolean(s,t,e){return e>.5?t:s},color(s,t,e){const a=Ha(s||za),i=a.valid&&Ha(t||za);return i&&i.valid?i.mix(a,e).hexString():t},number(s,t,e){return s+(t-s)*e}};class zw{constructor(t,e,a,i){const n=e[a];i=me([t.to,i,n,t.from]);const r=me([t.from,n,i]);this._active=!0,this._fn=t.fn||Rw[t.type||typeof r],this._easing=Se[t.easing]||Se.linear,this._start=Math.floor(Date.now()+(t.delay||0)),this._duration=this._total=Math.floor(t.duration),this._loop=!!t.loop,this._target=e,this._prop=a,this._from=r,this._to=i,this._promises=void 0}active(){return this._active}update(t,e,a){if(this._active){this._notify(!1);const i=this._target[this._prop],n=a-this._start,r=this._duration-n;this._start=a,this._duration=Math.floor(Math.max(r,t.duration)),this._total+=n,this._loop=!!t.loop,this._to=me([t.to,e,i,t.from]),this._from=me([t.from,i,e])}}cancel(){this._active&&(this.tick(Date.now()),this._active=!1,this._notify(!1))}tick(t){const e=t-this._start,a=this._duration,i=this._prop,n=this._from,r=this._loop,h=this._to;let c;if(this._active=n!==h&&(r||e<a),!this._active){this._target[i]=h,this._notify(!0);return}if(e<0){this._target[i]=n;return}c=e/a%2,c=r&&c>1?2-c:c,c=this._easing(Math.min(1,Math.max(0,c))),this._target[i]=this._fn(n,h,c)}wait(){const t=this._promises||(this._promises=[]);return new Promise((e,a)=>{t.push({res:e,rej:a})})}_notify(t){const e=t?"res":"rej",a=this._promises||[];for(let i=0;i<a.length;i++)a[i][e]()}}class xi{constructor(t,e){this._chart=t,this._properties=new Map,this.configure(e)}configure(t){if(!T(t))return;const e=Object.keys(W.animation),a=this._properties;Object.getOwnPropertyNames(t).forEach(i=>{const n=t[i];if(!T(n))return;const r={};for(const h of e)r[h]=n[h];(Z(n.properties)&&n.properties||[i]).forEach(h=>{(h===i||!a.has(h))&&a.set(h,r)})})}_animateOptions(t,e){const a=e.options,i=$w(t,a);if(!i)return[];const n=this._createAnimations(i,a);return a.$shared&&Iw(t.options.$animations,a).then(()=>{t.options=a},()=>{}),n}_createAnimations(t,e){const a=this._properties,i=[],n=t.$animations||(t.$animations={}),r=Object.keys(e),h=Date.now();let c;for(c=r.length-1;c>=0;--c){const l=r[c];if(l.charAt(0)==="$")continue;if(l==="options"){i.push(...this._animateOptions(t,e));continue}const d=e[l];let p=n[l];const g=a.get(l);if(p)if(g&&p.active()){p.update(g,d,h);continue}else p.cancel();if(!g||!g.duration){t[l]=d;continue}n[l]=p=new zw(g,t,l,d),i.push(p)}return i}update(t,e){if(this._properties.size===0){Object.assign(t,e);return}const a=this._createAnimations(t,e);if(a.length)return Mt.add(this._chart,a),!0}}function Iw(s,t){const e=[],a=Object.keys(t);for(let i=0;i<a.length;i++){const n=s[a[i]];n&&n.active()&&e.push(n.wait())}return Promise.all(e)}function $w(s,t){if(!t)return;let e=s.options;if(!e){s.options=t;return}return e.$shared&&(s.options=e=Object.assign({},e,{$shared:!1,$animations:{}})),e}function Ia(s,t){const e=s&&s.options||{},a=e.reverse,i=e.min===void 0?t:0,n=e.max===void 0?t:0;return{start:a?n:i,end:a?i:n}}function Zw(s,t,e){if(e===!1)return!1;const a=Ia(s,e),i=Ia(t,e);return{top:i.end,right:a.end,bottom:i.start,left:a.start}}function Ww(s){let t,e,a,i;return T(s)?(t=s.top,e=s.right,a=s.bottom,i=s.left):t=e=a=i=s,{top:t,right:e,bottom:a,left:i,disabled:s===!1}}function mi(s,t){const e=[],a=s._getSortedDatasetMetas(t);let i,n;for(i=0,n=a.length;i<n;++i)e.push(a[i].index);return e}function $a(s,t,e,a={}){const i=s.keys,n=a.mode==="single";let r,h,c,l;if(t===null)return;let d=!1;for(r=0,h=i.length;r<h;++r){if(c=+i[r],c===e){if(d=!0,a.all)continue;break}l=s.values[c],N(l)&&(n||t===0||xt(t)===xt(l))&&(t+=l)}return!d&&!a.all?0:t}function Nw(s,t){const{iScale:e,vScale:a}=t,i=e.axis==="x"?"x":"y",n=a.axis==="x"?"x":"y",r=Object.keys(s),h=new Array(r.length);let c,l,d;for(c=0,l=r.length;c<l;++c)d=r[c],h[c]={[i]:d,[n]:s[d]};return h}function T1(s,t){const e=s&&s.options.stacked;return e||e===void 0&&t.stack!==void 0}function jw(s,t,e){return`${s.id}.${t.id}.${e.stack||e.type}`}function Uw(s){const{min:t,max:e,minDefined:a,maxDefined:i}=s.getUserBounds();return{min:a?t:Number.NEGATIVE_INFINITY,max:i?e:Number.POSITIVE_INFINITY}}function qw(s,t,e){const a=s[t]||(s[t]={});return a[e]||(a[e]={})}function Za(s,t,e,a){for(const i of t.getMatchingVisibleMetas(a).reverse()){const n=s[i.index];if(e&&n>0||!e&&n<0)return i.index}return null}function Wa(s,t){const{chart:e,_cachedMeta:a}=s,i=e._stacks||(e._stacks={}),{iScale:n,vScale:r,index:h}=a,c=n.axis,l=r.axis,d=jw(n,r,a),p=t.length;let g;for(let u=0;u<p;++u){const f=t[u],{[c]:v,[l]:x}=f,m=f._stacks||(f._stacks={});g=m[l]=qw(i,d,v),g[h]=x,g._top=Za(g,r,!0,a.type),g._bottom=Za(g,r,!1,a.type);const M=g._visualValues||(g._visualValues={});M[h]=x}}function B1(s,t){const e=s.scales;return Object.keys(e).filter(a=>e[a].axis===t).shift()}function Gw(s,t){return Ft(s,{active:!1,dataset:void 0,datasetIndex:t,index:t,mode:"default",type:"dataset"})}function Xw(s,t,e){return Ft(s,{active:!1,dataIndex:t,parsed:void 0,raw:void 0,element:e,index:t,mode:"default",type:"data"})}function le(s,t){const e=s.controller.index,a=s.vScale&&s.vScale.axis;if(a){t=t||s._parsed;for(const i of t){const n=i._stacks;if(!n||n[a]===void 0||n[a][e]===void 0)return;delete n[a][e],n[a]._visualValues!==void 0&&n[a]._visualValues[e]!==void 0&&delete n[a]._visualValues[e]}}}const O1=s=>s==="reset"||s==="none",Na=(s,t)=>t?s:Object.assign({},s),Yw=(s,t,e)=>s&&!t.hidden&&t._stacked&&{keys:mi(e,!0),values:null};class lt{constructor(t,e){this.chart=t,this._ctx=t.ctx,this.index=e,this._cachedDataOpts={},this._cachedMeta=this.getMeta(),this._type=this._cachedMeta.type,this.options=void 0,this._parsing=!1,this._data=void 0,this._objectData=void 0,this._sharedOptions=void 0,this._drawStart=void 0,this._drawCount=void 0,this.enableOptionSharing=!1,this.supportsDecimation=!1,this.$context=void 0,this._syncList=[],this.datasetElementType=new.target.datasetElementType,this.dataElementType=new.target.dataElementType,this.initialize()}initialize(){const t=this._cachedMeta;this.configure(),this.linkScales(),t._stacked=T1(t.vScale,t),this.addElements(),this.options.fill&&!this.chart.isPluginEnabled("filler")&&console.warn("Tried to use the 'fill' option without the 'Filler' plugin enabled. Please import and register the 'Filler' plugin and make sure it is not disabled in the options")}updateIndex(t){this.index!==t&&le(this._cachedMeta),this.index=t}linkScales(){const t=this.chart,e=this._cachedMeta,a=this.getDataset(),i=(p,g,u,f)=>p==="x"?g:p==="r"?f:u,n=e.xAxisID=H(a.xAxisID,B1(t,"x")),r=e.yAxisID=H(a.yAxisID,B1(t,"y")),h=e.rAxisID=H(a.rAxisID,B1(t,"r")),c=e.indexAxis,l=e.iAxisID=i(c,n,r,h),d=e.vAxisID=i(c,r,n,h);e.xScale=this.getScaleForId(n),e.yScale=this.getScaleForId(r),e.rScale=this.getScaleForId(h),e.iScale=this.getScaleForId(l),e.vScale=this.getScaleForId(d)}getDataset(){return this.chart.data.datasets[this.index]}getMeta(){return this.chart.getDatasetMeta(this.index)}getScaleForId(t){return this.chart.scales[t]}_getOtherScale(t){const e=this._cachedMeta;return t===e.iScale?e.vScale:e.iScale}reset(){this._update("reset")}_destroy(){const t=this._cachedMeta;this._data&&Sa(this._data,this),t._stacked&&le(t)}_dataCheck(){const t=this.getDataset(),e=t.data||(t.data=[]),a=this._data;if(T(e)){const i=this._cachedMeta;this._data=Nw(e,i)}else if(a!==e){if(a){Sa(a,this);const i=this._cachedMeta;le(i),i._parsed=[]}e&&Object.isExtensible(e)&&Tb(e,this),this._syncList=[],this._data=e}}addElements(){const t=this._cachedMeta;this._dataCheck(),this.datasetElementType&&(t.dataset=new this.datasetElementType)}buildOrUpdateElements(t){const e=this._cachedMeta,a=this.getDataset();let i=!1;this._dataCheck();const n=e._stacked;e._stacked=T1(e.vScale,e),e.stack!==a.stack&&(i=!0,le(e),e.stack=a.stack),this._resyncElements(t),(i||n!==e._stacked)&&(Wa(this,e._parsed),e._stacked=T1(e.vScale,e))}configure(){const t=this.chart.config,e=t.datasetScopeKeys(this._type),a=t.getOptionScopes(this.getDataset(),e,!0);this.options=t.createResolver(a,this.getContext()),this._parsing=this.options.parsing,this._cachedDataOpts={}}parse(t,e){const{_cachedMeta:a,_data:i}=this,{iScale:n,_stacked:r}=a,h=n.axis;let c=t===0&&e===i.length?!0:a._sorted,l=t>0&&a._parsed[t-1],d,p,g;if(this._parsing===!1)a._parsed=i,a._sorted=!0,g=i;else{Z(i[t])?g=this.parseArrayData(a,i,t,e):T(i[t])?g=this.parseObjectData(a,i,t,e):g=this.parsePrimitiveData(a,i,t,e);const u=()=>p[h]===null||l&&p[h]<l[h];for(d=0;d<e;++d)a._parsed[d+t]=p=g[d],c&&(u()&&(c=!1),l=p);a._sorted=c}r&&Wa(this,g)}parsePrimitiveData(t,e,a,i){const{iScale:n,vScale:r}=t,h=n.axis,c=r.axis,l=n.getLabels(),d=n===r,p=new Array(i);let g,u,f;for(g=0,u=i;g<u;++g)f=g+a,p[g]={[h]:d||n.parse(l[f],f),[c]:r.parse(e[f],f)};return p}parseArrayData(t,e,a,i){const{xScale:n,yScale:r}=t,h=new Array(i);let c,l,d,p;for(c=0,l=i;c<l;++c)d=c+a,p=e[d],h[c]={x:n.parse(p[0],d),y:r.parse(p[1],d)};return h}parseObjectData(t,e,a,i){const{xScale:n,yScale:r}=t,{xAxisKey:h="x",yAxisKey:c="y"}=this._parsing,l=new Array(i);let d,p,g,u;for(d=0,p=i;d<p;++d)g=d+a,u=e[g],l[d]={x:n.parse(Pt(u,h),g),y:r.parse(Pt(u,c),g)};return l}getParsed(t){return this._cachedMeta._parsed[t]}getDataElement(t){return this._cachedMeta.data[t]}applyStack(t,e,a){const i=this.chart,n=this._cachedMeta,r=e[t.axis],h={keys:mi(i,!0),values:e._stacks[t.axis]._visualValues};return $a(h,r,n.index,{mode:a})}updateRangeFromParsed(t,e,a,i){const n=a[e.axis];let r=n===null?NaN:n;const h=i&&a._stacks[e.axis];i&&h&&(i.values=h,r=$a(i,n,this._cachedMeta.index)),t.min=Math.min(t.min,r),t.max=Math.max(t.max,r)}getMinMax(t,e){const a=this._cachedMeta,i=a._parsed,n=a._sorted&&t===a.iScale,r=i.length,h=this._getOtherScale(t),c=Yw(e,a,this.chart),l={min:Number.POSITIVE_INFINITY,max:Number.NEGATIVE_INFINITY},{min:d,max:p}=Uw(h);let g,u;function f(){u=i[g];const v=u[h.axis];return!N(u[t.axis])||d>v||p<v}for(g=0;g<r&&!(!f()&&(this.updateRangeFromParsed(l,t,u,c),n));++g);if(n){for(g=r-1;g>=0;--g)if(!f()){this.updateRangeFromParsed(l,t,u,c);break}}return l}getAllParsedValues(t){const e=this._cachedMeta._parsed,a=[];let i,n,r;for(i=0,n=e.length;i<n;++i)r=e[i][t.axis],N(r)&&a.push(r);return a}getMaxOverflow(){return!1}getLabelAndValue(t){const e=this._cachedMeta,a=e.iScale,i=e.vScale,n=this.getParsed(t);return{label:a?""+a.getLabelForValue(n[a.axis]):"",value:i?""+i.getLabelForValue(n[i.axis]):""}}_update(t){const e=this._cachedMeta;this.update(t||"default"),e._clip=Ww(H(this.options.clip,Zw(e.xScale,e.yScale,this.getMaxOverflow())))}update(t){}draw(){const t=this._ctx,e=this.chart,a=this._cachedMeta,i=a.data||[],n=e.chartArea,r=[],h=this._drawStart||0,c=this._drawCount||i.length-h,l=this.options.drawActiveElementsOnTop;let d;for(a.dataset&&a.dataset.draw(t,n,h,c),d=h;d<h+c;++d){const p=i[d];p.hidden||(p.active&&l?r.push(p):p.draw(t,n))}for(d=0;d<r.length;++d)r[d].draw(t,n)}getStyle(t,e){const a=e?"active":"default";return t===void 0&&this._cachedMeta.dataset?this.resolveDatasetElementOptions(a):this.resolveDataElementOptions(t||0,a)}getContext(t,e,a){const i=this.getDataset();let n;if(t>=0&&t<this._cachedMeta.data.length){const r=this._cachedMeta.data[t];n=r.$context||(r.$context=Xw(this.getContext(),t,r)),n.parsed=this.getParsed(t),n.raw=i.data[t],n.index=n.dataIndex=t}else n=this.$context||(this.$context=Gw(this.chart.getContext(),this.index)),n.dataset=i,n.index=n.datasetIndex=this.index;return n.active=!!e,n.mode=a,n}resolveDatasetElementOptions(t){return this._resolveElementOptions(this.datasetElementType.id,t)}resolveDataElementOptions(t,e){return this._resolveElementOptions(this.dataElementType.id,e,t)}_resolveElementOptions(t,e="default",a){const i=e==="active",n=this._cachedDataOpts,r=t+"-"+e,h=n[r],c=this.enableOptionSharing&&Te(a);if(h)return Na(h,c);const l=this.chart.config,d=l.datasetElementScopeKeys(this._type,t),p=i?[`${t}Hover`,"hover",t,""]:[t,""],g=l.getOptionScopes(this.getDataset(),d),u=Object.keys(W.elements[t]),f=()=>this.getContext(a,i,e),v=l.resolveNamedOptions(g,u,f,p);return v.$shared&&(v.$shared=c,n[r]=Object.freeze(Na(v,c))),v}_resolveAnimations(t,e,a){const i=this.chart,n=this._cachedDataOpts,r=`animation-${e}`,h=n[r];if(h)return h;let c;if(i.options.animation!==!1){const d=this.chart.config,p=d.datasetAnimationScopeKeys(this._type,e),g=d.getOptionScopes(this.getDataset(),p);c=d.createResolver(g,this.getContext(t,a,e))}const l=new xi(i,c&&c.animations);return c&&c._cacheable&&(n[r]=Object.freeze(l)),l}getSharedOptions(t){if(t.$shared)return this._sharedOptions||(this._sharedOptions=Object.assign({},t))}includeOptions(t,e){return!e||O1(t)||this.chart._animationsDisabled}_getSharedOptions(t,e){const a=this.resolveDataElementOptions(t,e),i=this._sharedOptions,n=this.getSharedOptions(a),r=this.includeOptions(e,n)||n!==i;return this.updateSharedOptions(n,e,a),{sharedOptions:n,includeOptions:r}}updateElement(t,e,a,i){O1(i)?Object.assign(t,a):this._resolveAnimations(e,i).update(t,a)}updateSharedOptions(t,e,a){t&&!O1(e)&&this._resolveAnimations(void 0,e).update(t,a)}_setStyle(t,e,a,i){t.active=i;const n=this.getStyle(e,i);this._resolveAnimations(e,a,i).update(t,{options:!i&&this.getSharedOptions(n)||n})}removeHoverStyle(t,e,a){this._setStyle(t,a,"active",!1)}setHoverStyle(t,e,a){this._setStyle(t,a,"active",!0)}_removeDatasetHoverStyle(){const t=this._cachedMeta.dataset;t&&this._setStyle(t,void 0,"active",!1)}_setDatasetHoverStyle(){const t=this._cachedMeta.dataset;t&&this._setStyle(t,void 0,"active",!0)}_resyncElements(t){const e=this._data,a=this._cachedMeta.data;for(const[h,c,l]of this._syncList)this[h](c,l);this._syncList=[];const i=a.length,n=e.length,r=Math.min(n,i);r&&this.parse(0,r),n>i?this._insertElements(i,n-i,t):n<i&&this._removeElements(n,i-n)}_insertElements(t,e,a=!0){const i=this._cachedMeta,n=i.data,r=t+e;let h;const c=l=>{for(l.length+=e,h=l.length-1;h>=r;h--)l[h]=l[h-e]};for(c(n),h=t;h<r;++h)n[h]=new this.dataElementType;this._parsing&&c(i._parsed),this.parse(t,e),a&&this.updateElements(n,t,e,"reset")}updateElements(t,e,a,i){}_removeElements(t,e){const a=this._cachedMeta;if(this._parsing){const i=a._parsed.splice(t,e);a._stacked&&le(a,i)}a.data.splice(t,e)}_sync(t){if(this._parsing)this._syncList.push(t);else{const[e,a,i]=t;this[e](a,i)}this.chart._dataChanges.push([this.index,...t])}_onDataPush(){const t=arguments.length;this._sync(["_insertElements",this.getDataset().data.length-t,t])}_onDataPop(){this._sync(["_removeElements",this._cachedMeta.data.length-1,1])}_onDataShift(){this._sync(["_removeElements",0,1])}_onDataSplice(t,e){e&&this._sync(["_removeElements",t,e]);const a=arguments.length-2;a&&this._sync(["_insertElements",t,a])}_onDataUnshift(){this._sync(["_insertElements",0,arguments.length])}}_(lt,"defaults",{}),_(lt,"datasetElementType",null),_(lt,"dataElementType",null);function Kw(s,t){if(!s._cache.$bar){const e=s.getMatchingVisibleMetas(t);let a=[];for(let i=0,n=e.length;i<n;i++)a=a.concat(e[i].controller.getAllParsedValues(s));s._cache.$bar=K2(a.sort((i,n)=>i-n))}return s._cache.$bar}function Jw(s){const t=s.iScale,e=Kw(t,s.type);let a=t._length,i,n,r,h;const c=()=>{r===32767||r===-32768||(Te(h)&&(a=Math.min(a,Math.abs(r-h)||a)),h=r)};for(i=0,n=e.length;i<n;++i)r=t.getPixelForValue(e[i]),c();for(h=void 0,i=0,n=t.ticks.length;i<n;++i)r=t.getPixelForTick(i),c();return a}function Qw(s,t,e,a){const i=e.barThickness;let n,r;return F(i)?(n=t.min*e.categoryPercentage,r=e.barPercentage):(n=i*a,r=1),{chunk:n/a,ratio:r,start:t.pixels[s]-n/2}}function t_(s,t,e,a){const i=t.pixels,n=i[s];let r=s>0?i[s-1]:null,h=s<i.length-1?i[s+1]:null;const c=e.categoryPercentage;r===null&&(r=n-(h===null?t.end-t.start:h-n)),h===null&&(h=n+n-r);const l=n-(n-Math.min(r,h))/2*c;return{chunk:Math.abs(h-r)/2*c/a,ratio:e.barPercentage,start:l}}function e_(s,t,e,a){const i=e.parse(s[0],a),n=e.parse(s[1],a),r=Math.min(i,n),h=Math.max(i,n);let c=r,l=h;Math.abs(r)>Math.abs(h)&&(c=h,l=r),t[e.axis]=l,t._custom={barStart:c,barEnd:l,start:i,end:n,min:r,max:h}}function Mi(s,t,e,a){return Z(s)?e_(s,t,e,a):t[e.axis]=e.parse(s,a),t}function ja(s,t,e,a){const i=s.iScale,n=s.vScale,r=i.getLabels(),h=i===n,c=[];let l,d,p,g;for(l=e,d=e+a;l<d;++l)g=t[l],p={},p[i.axis]=h||i.parse(r[l],l),c.push(Mi(g,p,n,l));return c}function E1(s){return s&&s.barStart!==void 0&&s.barEnd!==void 0}function s_(s,t,e){return s!==0?xt(s):(t.isHorizontal()?1:-1)*(t.min>=e?1:-1)}function a_(s){let t,e,a,i,n;return s.horizontal?(t=s.base>s.x,e="left",a="right"):(t=s.base<s.y,e="bottom",a="top"),t?(i="end",n="start"):(i="start",n="end"),{start:e,end:a,reverse:t,top:i,bottom:n}}function i_(s,t,e,a){let i=t.borderSkipped;const n={};if(!i){s.borderSkipped=n;return}if(i===!0){s.borderSkipped={top:!0,right:!0,bottom:!0,left:!0};return}const{start:r,end:h,reverse:c,top:l,bottom:d}=a_(s);i==="middle"&&e&&(s.enableBorderRadius=!0,(e._top||0)===a?i=l:(e._bottom||0)===a?i=d:(n[Ua(d,r,h,c)]=!0,i=l)),n[Ua(i,r,h,c)]=!0,s.borderSkipped=n}function Ua(s,t,e,a){return a?(s=n_(s,t,e),s=qa(s,e,t)):s=qa(s,t,e),s}function n_(s,t,e){return s===t?e:s===e?t:s}function qa(s,t,e){return s==="start"?t:s==="end"?e:s}function o_(s,{inflateAmount:t},e){s.inflateAmount=t==="auto"?e===1?.33:0:t}class n1 extends lt{parsePrimitiveData(t,e,a,i){return ja(t,e,a,i)}parseArrayData(t,e,a,i){return ja(t,e,a,i)}parseObjectData(t,e,a,i){const{iScale:n,vScale:r}=t,{xAxisKey:h="x",yAxisKey:c="y"}=this._parsing,l=n.axis==="x"?h:c,d=r.axis==="x"?h:c,p=[];let g,u,f,v;for(g=a,u=a+i;g<u;++g)v=e[g],f={},f[n.axis]=n.parse(Pt(v,l),g),p.push(Mi(Pt(v,d),f,r,g));return p}updateRangeFromParsed(t,e,a,i){super.updateRangeFromParsed(t,e,a,i);const n=a._custom;n&&e===this._cachedMeta.vScale&&(t.min=Math.min(t.min,n.min),t.max=Math.max(t.max,n.max))}getMaxOverflow(){return 0}getLabelAndValue(t){const e=this._cachedMeta,{iScale:a,vScale:i}=e,n=this.getParsed(t),r=n._custom,h=E1(r)?"["+r.start+", "+r.end+"]":""+i.getLabelForValue(n[i.axis]);return{label:""+a.getLabelForValue(n[a.axis]),value:h}}initialize(){this.enableOptionSharing=!0,super.initialize();const t=this._cachedMeta;t.stack=this.getDataset().stack}update(t){const e=this._cachedMeta;this.updateElements(e.data,0,e.data.length,t)}updateElements(t,e,a,i){const n=i==="reset",{index:r,_cachedMeta:{vScale:h}}=this,c=h.getBasePixel(),l=h.isHorizontal(),d=this._getRuler(),{sharedOptions:p,includeOptions:g}=this._getSharedOptions(e,i);for(let u=e;u<e+a;u++){const f=this.getParsed(u),v=n||F(f[h.axis])?{base:c,head:c}:this._calculateBarValuePixels(u),x=this._calculateBarIndexPixels(u,d),m=(f._stacks||{})[h.axis],M={horizontal:l,base:v.base,enableBorderRadius:!m||E1(f._custom)||r===m._top||r===m._bottom,x:l?v.head:x.center,y:l?x.center:v.head,height:l?x.size:Math.abs(v.size),width:l?Math.abs(v.size):x.size};g&&(M.options=p||this.resolveDataElementOptions(u,t[u].active?"active":i));const b=M.options||t[u].options;i_(M,b,m,r),o_(M,b,d.ratio),this.updateElement(t[u],u,M,i)}}_getStacks(t,e){const{iScale:a}=this._cachedMeta,i=a.getMatchingVisibleMetas(this._type).filter(d=>d.controller.options.grouped),n=a.options.stacked,r=[],h=this._cachedMeta.controller.getParsed(e),c=h&&h[a.axis],l=d=>{const p=d._parsed.find(u=>u[a.axis]===c),g=p&&p[d.vScale.axis];if(F(g)||isNaN(g))return!0};for(const d of i)if(!(e!==void 0&&l(d))&&((n===!1||r.indexOf(d.stack)===-1||n===void 0&&d.stack===void 0)&&r.push(d.stack),d.index===t))break;return r.length||r.push(void 0),r}_getStackCount(t){return this._getStacks(void 0,t).length}_getAxisCount(){return this._getAxis().length}getFirstScaleIdForIndexAxis(){const t=this.chart.scales,e=this.chart.options.indexAxis;return Object.keys(t).filter(a=>t[a].axis===e).shift()}_getAxis(){const t={},e=this.getFirstScaleIdForIndexAxis();for(const a of this.chart.data.datasets)t[H(this.chart.options.indexAxis==="x"?a.xAxisID:a.yAxisID,e)]=!0;return Object.keys(t)}_getStackIndex(t,e,a){const i=this._getStacks(t,a),n=e!==void 0?i.indexOf(e):-1;return n===-1?i.length-1:n}_getRuler(){const t=this.options,e=this._cachedMeta,a=e.iScale,i=[];let n,r;for(n=0,r=e.data.length;n<r;++n)i.push(a.getPixelForValue(this.getParsed(n)[a.axis],n));const h=t.barThickness;return{min:h||Jw(e),pixels:i,start:a._startPixel,end:a._endPixel,stackCount:this._getStackCount(),scale:a,grouped:t.grouped,ratio:h?1:t.categoryPercentage*t.barPercentage}}_calculateBarValuePixels(t){const{_cachedMeta:{vScale:e,_stacked:a,index:i},options:{base:n,minBarLength:r}}=this,h=n||0,c=this.getParsed(t),l=c._custom,d=E1(l);let p=c[e.axis],g=0,u=a?this.applyStack(e,c,a):p,f,v;u!==p&&(g=u-p,u=p),d&&(p=l.barStart,u=l.barEnd-l.barStart,p!==0&&xt(p)!==xt(l.barEnd)&&(g=0),g+=p);const x=!F(n)&&!d?n:g;let m=e.getPixelForValue(x);if(this.chart.getDataVisibility(t)?f=e.getPixelForValue(g+u):f=m,v=f-m,Math.abs(v)<r){v=s_(v,e,h)*r,p===h&&(m-=v/2);const M=e.getPixelForDecimal(0),b=e.getPixelForDecimal(1),w=Math.min(M,b),y=Math.max(M,b);m=Math.max(Math.min(m,y),w),f=m+v,a&&!d&&(c._stacks[e.axis]._visualValues[i]=e.getValueForPixel(f)-e.getValueForPixel(m))}if(m===e.getPixelForValue(h)){const M=xt(v)*e.getLineWidthForValue(h)/2;m+=M,v-=M}return{size:v,base:m,head:f,center:f+v/2}}_calculateBarIndexPixels(t,e){const a=e.scale,i=this.options,n=i.skipNull,r=H(i.maxBarThickness,1/0);let h,c;const l=this._getAxisCount();if(e.grouped){const d=n?this._getStackCount(t):e.stackCount,p=i.barThickness==="flex"?t_(t,e,i,d*l):Qw(t,e,i,d*l),g=this.chart.options.indexAxis==="x"?this.getDataset().xAxisID:this.getDataset().yAxisID,u=this._getAxis().indexOf(H(g,this.getFirstScaleIdForIndexAxis())),f=this._getStackIndex(this.index,this._cachedMeta.stack,n?t:void 0)+u;h=p.start+p.chunk*f+p.chunk/2,c=Math.min(r,p.chunk*p.ratio)}else h=a.getPixelForValue(this.getParsed(t)[a.axis],t),c=Math.min(r,e.min*e.ratio);return{base:h-c/2,head:h+c/2,center:h,size:c}}draw(){const t=this._cachedMeta,e=t.vScale,a=t.data,i=a.length;let n=0;for(;n<i;++n)this.getParsed(n)[e.axis]!==null&&!a[n].hidden&&a[n].draw(this._ctx)}}_(n1,"id","bar"),_(n1,"defaults",{datasetElementType:!1,dataElementType:"bar",categoryPercentage:.8,barPercentage:.9,grouped:!0,animations:{numbers:{type:"number",properties:["x","y","base","width","height"]}}}),_(n1,"overrides",{scales:{_index_:{type:"category",offset:!0,grid:{offset:!0}},_value_:{type:"linear",beginAtZero:!0}}});class o1 extends lt{initialize(){this.enableOptionSharing=!0,super.initialize()}parsePrimitiveData(t,e,a,i){const n=super.parsePrimitiveData(t,e,a,i);for(let r=0;r<n.length;r++)n[r]._custom=this.resolveDataElementOptions(r+a).radius;return n}parseArrayData(t,e,a,i){const n=super.parseArrayData(t,e,a,i);for(let r=0;r<n.length;r++){const h=e[a+r];n[r]._custom=H(h[2],this.resolveDataElementOptions(r+a).radius)}return n}parseObjectData(t,e,a,i){const n=super.parseObjectData(t,e,a,i);for(let r=0;r<n.length;r++){const h=e[a+r];n[r]._custom=H(h&&h.r&&+h.r,this.resolveDataElementOptions(r+a).radius)}return n}getMaxOverflow(){const t=this._cachedMeta.data;let e=0;for(let a=t.length-1;a>=0;--a)e=Math.max(e,t[a].size(this.resolveDataElementOptions(a))/2);return e>0&&e}getLabelAndValue(t){const e=this._cachedMeta,a=this.chart.data.labels||[],{xScale:i,yScale:n}=e,r=this.getParsed(t),h=i.getLabelForValue(r.x),c=n.getLabelForValue(r.y),l=r._custom;return{label:a[t]||"",value:"("+h+", "+c+(l?", "+l:"")+")"}}update(t){const e=this._cachedMeta.data;this.updateElements(e,0,e.length,t)}updateElements(t,e,a,i){const n=i==="reset",{iScale:r,vScale:h}=this._cachedMeta,{sharedOptions:c,includeOptions:l}=this._getSharedOptions(e,i),d=r.axis,p=h.axis;for(let g=e;g<e+a;g++){const u=t[g],f=!n&&this.getParsed(g),v={},x=v[d]=n?r.getPixelForDecimal(.5):r.getPixelForValue(f[d]),m=v[p]=n?h.getBasePixel():h.getPixelForValue(f[p]);v.skip=isNaN(x)||isNaN(m),l&&(v.options=c||this.resolveDataElementOptions(g,u.active?"active":i),n&&(v.options.radius=0)),this.updateElement(u,g,v,i)}}resolveDataElementOptions(t,e){const a=this.getParsed(t);let i=super.resolveDataElementOptions(t,e);i.$shared&&(i=Object.assign({},i,{$shared:!1}));const n=i.radius;return e!=="active"&&(i.radius=0),i.radius+=H(a&&a._custom,n),i}}_(o1,"id","bubble"),_(o1,"defaults",{datasetElementType:!1,dataElementType:"point",animations:{numbers:{type:"number",properties:["x","y","borderWidth","radius"]}}}),_(o1,"overrides",{scales:{x:{type:"linear"},y:{type:"linear"}}});function r_(s,t,e){let a=1,i=1,n=0,r=0;if(t<I){const h=s,c=h+t,l=Math.cos(h),d=Math.sin(h),p=Math.cos(c),g=Math.sin(c),u=(b,w,y)=>Be(b,h,c,!0)?1:Math.max(w,w*e,y,y*e),f=(b,w,y)=>Be(b,h,c,!0)?-1:Math.min(w,w*e,y,y*e),v=u(0,l,p),x=u(U,d,g),m=f(O,l,p),M=f(O+U,d,g);a=(v-m)/2,i=(x-M)/2,n=-(v+m)/2,r=-(x+M)/2}return{ratioX:a,ratioY:i,offsetX:n,offsetY:r}}class Nt extends lt{constructor(t,e){super(t,e),this.enableOptionSharing=!0,this.innerRadius=void 0,this.outerRadius=void 0,this.offsetX=void 0,this.offsetY=void 0}linkScales(){}parse(t,e){const a=this.getDataset().data,i=this._cachedMeta;if(this._parsing===!1)i._parsed=a;else{let n=c=>+a[c];if(T(a[t])){const{key:c="value"}=this._parsing;n=l=>+Pt(a[l],c)}let r,h;for(r=t,h=t+e;r<h;++r)i._parsed[r]=n(r)}}_getRotation(){return ct(this.options.rotation-90)}_getCircumference(){return ct(this.options.circumference)}_getRotationExtents(){let t=I,e=-I;for(let a=0;a<this.chart.data.datasets.length;++a)if(this.chart.isDatasetVisible(a)&&this.chart.getDatasetMeta(a).type===this._type){const i=this.chart.getDatasetMeta(a).controller,n=i._getRotation(),r=i._getCircumference();t=Math.min(t,n),e=Math.max(e,n+r)}return{rotation:t,circumference:e-t}}update(t){const e=this.chart,{chartArea:a}=e,i=this._cachedMeta,n=i.data,r=this.getMaxBorderWidth()+this.getMaxOffset(n)+this.options.spacing,h=Math.max((Math.min(a.width,a.height)-r)/2,0),c=Math.min(Mb(this.options.cutout,h),1),l=this._getRingWeight(this.index),{circumference:d,rotation:p}=this._getRotationExtents(),{ratioX:g,ratioY:u,offsetX:f,offsetY:v}=r_(p,d,c),x=(a.width-r)/g,m=(a.height-r)/u,M=Math.max(Math.min(x,m)/2,0),b=U2(this.options.radius,M),w=Math.max(b*c,0),y=(b-w)/this._getVisibleDatasetWeightTotal();this.offsetX=f*b,this.offsetY=v*b,i.total=this.calculateTotal(),this.outerRadius=b-y*this._getRingWeightOffset(this.index),this.innerRadius=Math.max(this.outerRadius-y*l,0),this.updateElements(n,0,n.length,t)}_circumference(t,e){const a=this.options,i=this._cachedMeta,n=this._getCircumference();return e&&a.animation.animateRotate||!this.chart.getDataVisibility(t)||i._parsed[t]===null||i.data[t].hidden?0:this.calculateCircumference(i._parsed[t]*n/I)}updateElements(t,e,a,i){const n=i==="reset",r=this.chart,h=r.chartArea,l=r.options.animation,d=(h.left+h.right)/2,p=(h.top+h.bottom)/2,g=n&&l.animateScale,u=g?0:this.innerRadius,f=g?0:this.outerRadius,{sharedOptions:v,includeOptions:x}=this._getSharedOptions(e,i);let m=this._getRotation(),M;for(M=0;M<e;++M)m+=this._circumference(M,n);for(M=e;M<e+a;++M){const b=this._circumference(M,n),w=t[M],y={x:d+this.offsetX,y:p+this.offsetY,startAngle:m,endAngle:m+b,circumference:b,outerRadius:f,innerRadius:u};x&&(y.options=v||this.resolveDataElementOptions(M,w.active?"active":i)),m+=b,this.updateElement(w,M,y,i)}}calculateTotal(){const t=this._cachedMeta,e=t.data;let a=0,i;for(i=0;i<e.length;i++){const n=t._parsed[i];n!==null&&!isNaN(n)&&this.chart.getDataVisibility(i)&&!e[i].hidden&&(a+=Math.abs(n))}return a}calculateCircumference(t){const e=this._cachedMeta.total;return e>0&&!isNaN(t)?I*(Math.abs(t)/e):0}getLabelAndValue(t){const e=this._cachedMeta,a=this.chart,i=a.data.labels||[],n=$e(e._parsed[t],a.options.locale);return{label:i[t]||"",value:n}}getMaxBorderWidth(t){let e=0;const a=this.chart;let i,n,r,h,c;if(!t){for(i=0,n=a.data.datasets.length;i<n;++i)if(a.isDatasetVisible(i)){r=a.getDatasetMeta(i),t=r.data,h=r.controller;break}}if(!t)return 0;for(i=0,n=t.length;i<n;++i)c=h.resolveDataElementOptions(i),c.borderAlign!=="inner"&&(e=Math.max(e,c.borderWidth||0,c.hoverBorderWidth||0));return e}getMaxOffset(t){let e=0;for(let a=0,i=t.length;a<i;++a){const n=this.resolveDataElementOptions(a);e=Math.max(e,n.offset||0,n.hoverOffset||0)}return e}_getRingWeightOffset(t){let e=0;for(let a=0;a<t;++a)this.chart.isDatasetVisible(a)&&(e+=this._getRingWeight(a));return e}_getRingWeight(t){return Math.max(H(this.chart.data.datasets[t].weight,1),0)}_getVisibleDatasetWeightTotal(){return this._getRingWeightOffset(this.chart.data.datasets.length)||1}}_(Nt,"id","doughnut"),_(Nt,"defaults",{datasetElementType:!1,dataElementType:"arc",animation:{animateRotate:!0,animateScale:!1},animations:{numbers:{type:"number",properties:["circumference","endAngle","innerRadius","outerRadius","startAngle","x","y","offset","borderWidth","spacing"]}},cutout:"50%",rotation:0,circumference:360,radius:"100%",spacing:0,indexAxis:"r"}),_(Nt,"descriptors",{_scriptable:t=>t!=="spacing",_indexable:t=>t!=="spacing"&&!t.startsWith("borderDash")&&!t.startsWith("hoverBorderDash")}),_(Nt,"overrides",{aspectRatio:1,plugins:{legend:{labels:{generateLabels(t){const e=t.data,{labels:{pointStyle:a,textAlign:i,color:n,useBorderRadius:r,borderRadius:h}}=t.legend.options;return e.labels.length&&e.datasets.length?e.labels.map((c,l)=>{const p=t.getDatasetMeta(0).controller.getStyle(l);return{text:c,fillStyle:p.backgroundColor,fontColor:n,hidden:!t.getDataVisibility(l),lineDash:p.borderDash,lineDashOffset:p.borderDashOffset,lineJoin:p.borderJoinStyle,lineWidth:p.borderWidth,strokeStyle:p.borderColor,textAlign:i,pointStyle:a,borderRadius:r&&(h||p.borderRadius),index:l}}):[]}},onClick(t,e,a){a.chart.toggleDataVisibility(e.index),a.chart.update()}}}});class Ae extends lt{initialize(){this.enableOptionSharing=!0,this.supportsDecimation=!0,super.initialize()}update(t){const e=this._cachedMeta,{dataset:a,data:i=[],_dataset:n}=e,r=this.chart._animationsDisabled;let{start:h,count:c}=ti(e,i,r);this._drawStart=h,this._drawCount=c,ei(e)&&(h=0,c=i.length),a._chart=this.chart,a._datasetIndex=this.index,a._decimated=!!n._decimated,a.points=i;const l=this.resolveDatasetElementOptions(t);this.options.showLine||(l.borderWidth=0),l.segment=this.options.segment,this.updateElement(a,void 0,{animated:!r,options:l},t),this.updateElements(i,h,c,t)}updateElements(t,e,a,i){const n=i==="reset",{iScale:r,vScale:h,_stacked:c,_dataset:l}=this._cachedMeta,{sharedOptions:d,includeOptions:p}=this._getSharedOptions(e,i),g=r.axis,u=h.axis,{spanGaps:f,segment:v}=this.options,x=ae(f)?f:Number.POSITIVE_INFINITY,m=this.chart._animationsDisabled||n||i==="none",M=e+a,b=t.length;let w=e>0&&this.getParsed(e-1);for(let y=0;y<b;++y){const k=t[y],C=m?k:{};if(y<e||y>=M){C.skip=!0;continue}const S=this.getParsed(y),L=F(S[u]),P=C[g]=r.getPixelForValue(S[g],y),D=C[u]=n||L?h.getBasePixel():h.getPixelForValue(c?this.applyStack(h,S,c):S[u],y);C.skip=isNaN(P)||isNaN(D)||L,C.stop=y>0&&Math.abs(S[g]-w[g])>x,v&&(C.parsed=S,C.raw=l.data[y]),p&&(C.options=d||this.resolveDataElementOptions(y,k.active?"active":i)),m||this.updateElement(k,y,C,i),w=S}}getMaxOverflow(){const t=this._cachedMeta,e=t.dataset,a=e.options&&e.options.borderWidth||0,i=t.data||[];if(!i.length)return a;const n=i[0].size(this.resolveDataElementOptions(0)),r=i[i.length-1].size(this.resolveDataElementOptions(i.length-1));return Math.max(a,n,r)/2}draw(){const t=this._cachedMeta;t.dataset.updateControlPoints(this.chart.chartArea,t.iScale.axis),super.draw()}}_(Ae,"id","line"),_(Ae,"defaults",{datasetElementType:"line",dataElementType:"point",showLine:!0,spanGaps:!1}),_(Ae,"overrides",{scales:{_index_:{type:"category"},_value_:{type:"linear"}}});class He extends lt{constructor(t,e){super(t,e),this.innerRadius=void 0,this.outerRadius=void 0}getLabelAndValue(t){const e=this._cachedMeta,a=this.chart,i=a.data.labels||[],n=$e(e._parsed[t].r,a.options.locale);return{label:i[t]||"",value:n}}parseObjectData(t,e,a,i){return ci.bind(this)(t,e,a,i)}update(t){const e=this._cachedMeta.data;this._updateRadius(),this.updateElements(e,0,e.length,t)}getMinMax(){const t=this._cachedMeta,e={min:Number.POSITIVE_INFINITY,max:Number.NEGATIVE_INFINITY};return t.data.forEach((a,i)=>{const n=this.getParsed(i).r;!isNaN(n)&&this.chart.getDataVisibility(i)&&(n<e.min&&(e.min=n),n>e.max&&(e.max=n))}),e}_updateRadius(){const t=this.chart,e=t.chartArea,a=t.options,i=Math.min(e.right-e.left,e.bottom-e.top),n=Math.max(i/2,0),r=Math.max(a.cutoutPercentage?n/100*a.cutoutPercentage:1,0),h=(n-r)/t.getVisibleDatasetCount();this.outerRadius=n-h*this.index,this.innerRadius=this.outerRadius-h}updateElements(t,e,a,i){const n=i==="reset",r=this.chart,c=r.options.animation,l=this._cachedMeta.rScale,d=l.xCenter,p=l.yCenter,g=l.getIndexAngle(0)-.5*O;let u=g,f;const v=360/this.countVisibleElements();for(f=0;f<e;++f)u+=this._computeAngle(f,i,v);for(f=e;f<e+a;f++){const x=t[f];let m=u,M=u+this._computeAngle(f,i,v),b=r.getDataVisibility(f)?l.getDistanceFromCenterForValue(this.getParsed(f).r):0;u=M,n&&(c.animateScale&&(b=0),c.animateRotate&&(m=M=g));const w={x:d,y:p,innerRadius:0,outerRadius:b,startAngle:m,endAngle:M,options:this.resolveDataElementOptions(f,x.active?"active":i)};this.updateElement(x,f,w,i)}}countVisibleElements(){const t=this._cachedMeta;let e=0;return t.data.forEach((a,i)=>{!isNaN(this.getParsed(i).r)&&this.chart.getDataVisibility(i)&&e++}),e}_computeAngle(t,e,a){return this.chart.getDataVisibility(t)?ct(this.resolveDataElementOptions(t,e).angle||a):0}}_(He,"id","polarArea"),_(He,"defaults",{dataElementType:"arc",animation:{animateRotate:!0,animateScale:!0},animations:{numbers:{type:"number",properties:["x","y","startAngle","endAngle","innerRadius","outerRadius"]}},indexAxis:"r",startAngle:0}),_(He,"overrides",{aspectRatio:1,plugins:{legend:{labels:{generateLabels(t){const e=t.data;if(e.labels.length&&e.datasets.length){const{labels:{pointStyle:a,color:i}}=t.legend.options;return e.labels.map((n,r)=>{const c=t.getDatasetMeta(0).controller.getStyle(r);return{text:n,fillStyle:c.backgroundColor,strokeStyle:c.borderColor,fontColor:i,lineWidth:c.borderWidth,pointStyle:a,hidden:!t.getDataVisibility(r),index:r}})}return[]}},onClick(t,e,a){a.chart.toggleDataVisibility(e.index),a.chart.update()}}},scales:{r:{type:"radialLinear",angleLines:{display:!1},beginAtZero:!0,grid:{circular:!0},pointLabels:{display:!1},startAngle:0}}});class Y1 extends Nt{}_(Y1,"id","pie"),_(Y1,"defaults",{cutout:0,rotation:0,circumference:360,radius:"100%"});class r1 extends lt{getLabelAndValue(t){const e=this._cachedMeta.vScale,a=this.getParsed(t);return{label:e.getLabels()[t],value:""+e.getLabelForValue(a[e.axis])}}parseObjectData(t,e,a,i){return ci.bind(this)(t,e,a,i)}update(t){const e=this._cachedMeta,a=e.dataset,i=e.data||[],n=e.iScale.getLabels();if(a.points=i,t!=="resize"){const r=this.resolveDatasetElementOptions(t);this.options.showLine||(r.borderWidth=0);const h={_loop:!0,_fullLoop:n.length===i.length,options:r};this.updateElement(a,void 0,h,t)}this.updateElements(i,0,i.length,t)}updateElements(t,e,a,i){const n=this._cachedMeta.rScale,r=i==="reset";for(let h=e;h<e+a;h++){const c=t[h],l=this.resolveDataElementOptions(h,c.active?"active":i),d=n.getPointPositionForValue(h,this.getParsed(h).r),p=r?n.xCenter:d.x,g=r?n.yCenter:d.y,u={x:p,y:g,angle:d.angle,skip:isNaN(p)||isNaN(g),options:l};this.updateElement(c,h,u,i)}}}_(r1,"id","radar"),_(r1,"defaults",{datasetElementType:"line",dataElementType:"point",indexAxis:"r",showLine:!0,elements:{line:{fill:"start"}}}),_(r1,"overrides",{aspectRatio:1,scales:{r:{type:"radialLinear"}}});class h1 extends lt{getLabelAndValue(t){const e=this._cachedMeta,a=this.chart.data.labels||[],{xScale:i,yScale:n}=e,r=this.getParsed(t),h=i.getLabelForValue(r.x),c=n.getLabelForValue(r.y);return{label:a[t]||"",value:"("+h+", "+c+")"}}update(t){const e=this._cachedMeta,{data:a=[]}=e,i=this.chart._animationsDisabled;let{start:n,count:r}=ti(e,a,i);if(this._drawStart=n,this._drawCount=r,ei(e)&&(n=0,r=a.length),this.options.showLine){this.datasetElementType||this.addElements();const{dataset:h,_dataset:c}=e;h._chart=this.chart,h._datasetIndex=this.index,h._decimated=!!c._decimated,h.points=a;const l=this.resolveDatasetElementOptions(t);l.segment=this.options.segment,this.updateElement(h,void 0,{animated:!i,options:l},t)}else this.datasetElementType&&(delete e.dataset,this.datasetElementType=!1);this.updateElements(a,n,r,t)}addElements(){const{showLine:t}=this.options;!this.datasetElementType&&t&&(this.datasetElementType=this.chart.registry.getElement("line")),super.addElements()}updateElements(t,e,a,i){const n=i==="reset",{iScale:r,vScale:h,_stacked:c,_dataset:l}=this._cachedMeta,d=this.resolveDataElementOptions(e,i),p=this.getSharedOptions(d),g=this.includeOptions(i,p),u=r.axis,f=h.axis,{spanGaps:v,segment:x}=this.options,m=ae(v)?v:Number.POSITIVE_INFINITY,M=this.chart._animationsDisabled||n||i==="none";let b=e>0&&this.getParsed(e-1);for(let w=e;w<e+a;++w){const y=t[w],k=this.getParsed(w),C=M?y:{},S=F(k[f]),L=C[u]=r.getPixelForValue(k[u],w),P=C[f]=n||S?h.getBasePixel():h.getPixelForValue(c?this.applyStack(h,k,c):k[f],w);C.skip=isNaN(L)||isNaN(P)||S,C.stop=w>0&&Math.abs(k[u]-b[u])>m,x&&(C.parsed=k,C.raw=l.data[w]),g&&(C.options=p||this.resolveDataElementOptions(w,y.active?"active":i)),M||this.updateElement(y,w,C,i),b=k}this.updateSharedOptions(p,i,d)}getMaxOverflow(){const t=this._cachedMeta,e=t.data||[];if(!this.options.showLine){let h=0;for(let c=e.length-1;c>=0;--c)h=Math.max(h,e[c].size(this.resolveDataElementOptions(c))/2);return h>0&&h}const a=t.dataset,i=a.options&&a.options.borderWidth||0;if(!e.length)return i;const n=e[0].size(this.resolveDataElementOptions(0)),r=e[e.length-1].size(this.resolveDataElementOptions(e.length-1));return Math.max(i,n,r)/2}}_(h1,"id","scatter"),_(h1,"defaults",{datasetElementType:!1,dataElementType:"point",showLine:!1,fill:!1}),_(h1,"overrides",{interaction:{mode:"point"},scales:{x:{type:"linear"},y:{type:"linear"}}});var h_=Object.freeze({__proto__:null,BarController:n1,BubbleController:o1,DoughnutController:Nt,LineController:Ae,PieController:Y1,PolarAreaController:He,RadarController:r1,ScatterController:h1});function Rt(){throw new Error("This method is not implemented: Check that a complete date adapter is provided.")}class ys{constructor(t){_(this,"options");this.options=t||{}}static override(t){Object.assign(ys.prototype,t)}init(){}formats(){return Rt()}parse(){return Rt()}format(){return Rt()}add(){return Rt()}diff(){return Rt()}startOf(){return Rt()}endOf(){return Rt()}}var c_={_date:ys};function l_(s,t,e,a){const{controller:i,data:n,_sorted:r}=s,h=i._cachedMeta.iScale,c=s.dataset&&s.dataset.options?s.dataset.options.spanGaps:null;if(h&&t===h.axis&&t!=="r"&&r&&n.length){const l=h._reversePixels?Db:_t;if(a){if(i._sharedOptions){const d=n[0],p=typeof d.getRange=="function"&&d.getRange(t);if(p){const g=l(n,t,e-p),u=l(n,t,e+p);return{lo:g.lo,hi:u.hi}}}}else{const d=l(n,t,e);if(c){const{vScale:p}=i._cachedMeta,{_parsed:g}=s,u=g.slice(0,d.lo+1).reverse().findIndex(v=>!F(v[p.axis]));d.lo-=Math.max(0,u);const f=g.slice(d.hi).findIndex(v=>!F(v[p.axis]));d.hi+=Math.max(0,f)}return d}}return{lo:0,hi:n.length-1}}function S1(s,t,e,a,i){const n=s.getSortedVisibleDatasetMetas(),r=e[t];for(let h=0,c=n.length;h<c;++h){const{index:l,data:d}=n[h],{lo:p,hi:g}=l_(n[h],t,r,i);for(let u=p;u<=g;++u){const f=d[u];f.skip||a(f,l,u)}}}function d_(s){const t=s.indexOf("x")!==-1,e=s.indexOf("y")!==-1;return function(a,i){const n=t?Math.abs(a.x-i.x):0,r=e?Math.abs(a.y-i.y):0;return Math.sqrt(Math.pow(n,2)+Math.pow(r,2))}}function R1(s,t,e,a,i){const n=[];return!i&&!s.isPointInArea(t)||S1(s,e,t,function(h,c,l){!i&&!kt(h,s.chartArea,0)||h.inRange(t.x,t.y,a)&&n.push({element:h,datasetIndex:c,index:l})},!0),n}function p_(s,t,e,a){let i=[];function n(r,h,c){const{startAngle:l,endAngle:d}=r.getProps(["startAngle","endAngle"],a),{angle:p}=X2(r,{x:t.x,y:t.y});Be(p,l,d)&&i.push({element:r,datasetIndex:h,index:c})}return S1(s,e,t,n),i}function g_(s,t,e,a,i,n){let r=[];const h=d_(e);let c=Number.POSITIVE_INFINITY;function l(d,p,g){const u=d.inRange(t.x,t.y,i);if(a&&!u)return;const f=d.getCenterPoint(i);if(!(!!n||s.isPointInArea(f))&&!u)return;const x=h(t,f);x<c?(r=[{element:d,datasetIndex:p,index:g}],c=x):x===c&&r.push({element:d,datasetIndex:p,index:g})}return S1(s,e,t,l),r}function z1(s,t,e,a,i,n){return!n&&!s.isPointInArea(t)?[]:e==="r"&&!a?p_(s,t,e,i):g_(s,t,e,a,i,n)}function Ga(s,t,e,a,i){const n=[],r=e==="x"?"inXRange":"inYRange";let h=!1;return S1(s,e,t,(c,l,d)=>{c[r]&&c[r](t[e],i)&&(n.push({element:c,datasetIndex:l,index:d}),h=h||c.inRange(t.x,t.y,i))}),a&&!h?[]:n}var u_={modes:{index(s,t,e,a){const i=It(t,s),n=e.axis||"x",r=e.includeInvisible||!1,h=e.intersect?R1(s,i,n,a,r):z1(s,i,n,!1,a,r),c=[];return h.length?(s.getSortedVisibleDatasetMetas().forEach(l=>{const d=h[0].index,p=l.data[d];p&&!p.skip&&c.push({element:p,datasetIndex:l.index,index:d})}),c):[]},dataset(s,t,e,a){const i=It(t,s),n=e.axis||"xy",r=e.includeInvisible||!1;let h=e.intersect?R1(s,i,n,a,r):z1(s,i,n,!1,a,r);if(h.length>0){const c=h[0].datasetIndex,l=s.getDatasetMeta(c).data;h=[];for(let d=0;d<l.length;++d)h.push({element:l[d],datasetIndex:c,index:d})}return h},point(s,t,e,a){const i=It(t,s),n=e.axis||"xy",r=e.includeInvisible||!1;return R1(s,i,n,a,r)},nearest(s,t,e,a){const i=It(t,s),n=e.axis||"xy",r=e.includeInvisible||!1;return z1(s,i,n,e.intersect,a,r)},x(s,t,e,a){const i=It(t,s);return Ga(s,i,"x",e.intersect,a)},y(s,t,e,a){const i=It(t,s);return Ga(s,i,"y",e.intersect,a)}}};const yi=["left","top","right","bottom"];function de(s,t){return s.filter(e=>e.pos===t)}function Xa(s,t){return s.filter(e=>yi.indexOf(e.pos)===-1&&e.box.axis===t)}function pe(s,t){return s.sort((e,a)=>{const i=t?a:e,n=t?e:a;return i.weight===n.weight?i.index-n.index:i.weight-n.weight})}function f_(s){const t=[];let e,a,i,n,r,h;for(e=0,a=(s||[]).length;e<a;++e)i=s[e],{position:n,options:{stack:r,stackWeight:h=1}}=i,t.push({index:e,box:i,pos:n,horizontal:i.isHorizontal(),weight:i.weight,stack:r&&n+r,stackWeight:h});return t}function v_(s){const t={};for(const e of s){const{stack:a,pos:i,stackWeight:n}=e;if(!a||!yi.includes(i))continue;const r=t[a]||(t[a]={count:0,placed:0,weight:0,size:0});r.count++,r.weight+=n}return t}function x_(s,t){const e=v_(s),{vBoxMaxWidth:a,hBoxMaxHeight:i}=t;let n,r,h;for(n=0,r=s.length;n<r;++n){h=s[n];const{fullSize:c}=h.box,l=e[h.stack],d=l&&h.stackWeight/l.weight;h.horizontal?(h.width=d?d*a:c&&t.availableWidth,h.height=i):(h.width=a,h.height=d?d*i:c&&t.availableHeight)}return e}function m_(s){const t=f_(s),e=pe(t.filter(l=>l.box.fullSize),!0),a=pe(de(t,"left"),!0),i=pe(de(t,"right")),n=pe(de(t,"top"),!0),r=pe(de(t,"bottom")),h=Xa(t,"x"),c=Xa(t,"y");return{fullSize:e,leftAndTop:a.concat(n),rightAndBottom:i.concat(c).concat(r).concat(h),chartArea:de(t,"chartArea"),vertical:a.concat(i).concat(c),horizontal:n.concat(r).concat(h)}}function Ya(s,t,e,a){return Math.max(s[e],t[e])+Math.max(s[a],t[a])}function bi(s,t){s.top=Math.max(s.top,t.top),s.left=Math.max(s.left,t.left),s.bottom=Math.max(s.bottom,t.bottom),s.right=Math.max(s.right,t.right)}function M_(s,t,e,a){const{pos:i,box:n}=e,r=s.maxPadding;if(!T(i)){e.size&&(s[i]-=e.size);const p=a[e.stack]||{size:0,count:1};p.size=Math.max(p.size,e.horizontal?n.height:n.width),e.size=p.size/p.count,s[i]+=e.size}n.getPadding&&bi(r,n.getPadding());const h=Math.max(0,t.outerWidth-Ya(r,s,"left","right")),c=Math.max(0,t.outerHeight-Ya(r,s,"top","bottom")),l=h!==s.w,d=c!==s.h;return s.w=h,s.h=c,e.horizontal?{same:l,other:d}:{same:d,other:l}}function y_(s){const t=s.maxPadding;function e(a){const i=Math.max(t[a]-s[a],0);return s[a]+=i,i}s.y+=e("top"),s.x+=e("left"),e("right"),e("bottom")}function b_(s,t){const e=t.maxPadding;function a(i){const n={left:0,top:0,right:0,bottom:0};return i.forEach(r=>{n[r]=Math.max(t[r],e[r])}),n}return a(s?["left","right"]:["top","bottom"])}function Me(s,t,e,a){const i=[];let n,r,h,c,l,d;for(n=0,r=s.length,l=0;n<r;++n){h=s[n],c=h.box,c.update(h.width||t.w,h.height||t.h,b_(h.horizontal,t));const{same:p,other:g}=M_(t,e,h,a);l|=p&&i.length,d=d||g,c.fullSize||i.push(h)}return l&&Me(i,t,e,a)||d}function Ye(s,t,e,a,i){s.top=e,s.left=t,s.right=t+a,s.bottom=e+i,s.width=a,s.height=i}function Ka(s,t,e,a){const i=e.padding;let{x:n,y:r}=t;for(const h of s){const c=h.box,l=a[h.stack]||{placed:0,weight:1},d=h.stackWeight/l.weight||1;if(h.horizontal){const p=t.w*d,g=l.size||c.height;Te(l.start)&&(r=l.start),c.fullSize?Ye(c,i.left,r,e.outerWidth-i.right-i.left,g):Ye(c,t.left+l.placed,r,p,g),l.start=r,l.placed+=p,r=c.bottom}else{const p=t.h*d,g=l.size||c.width;Te(l.start)&&(n=l.start),c.fullSize?Ye(c,n,i.top,g,e.outerHeight-i.bottom-i.top):Ye(c,n,t.top+l.placed,g,p),l.start=n,l.placed+=p,n=c.right}}t.x=n,t.y=r}var tt={addBox(s,t){s.boxes||(s.boxes=[]),t.fullSize=t.fullSize||!1,t.position=t.position||"top",t.weight=t.weight||0,t._layers=t._layers||function(){return[{z:0,draw(e){t.draw(e)}}]},s.boxes.push(t)},removeBox(s,t){const e=s.boxes?s.boxes.indexOf(t):-1;e!==-1&&s.boxes.splice(e,1)},configure(s,t,e){t.fullSize=e.fullSize,t.position=e.position,t.weight=e.weight},update(s,t,e,a){if(!s)return;const i=et(s.options.layout.padding),n=Math.max(t-i.width,0),r=Math.max(e-i.height,0),h=m_(s.boxes),c=h.vertical,l=h.horizontal;E(s.boxes,v=>{typeof v.beforeLayout=="function"&&v.beforeLayout()});const d=c.reduce((v,x)=>x.box.options&&x.box.options.display===!1?v:v+1,0)||1,p=Object.freeze({outerWidth:t,outerHeight:e,padding:i,availableWidth:n,availableHeight:r,vBoxMaxWidth:n/2/d,hBoxMaxHeight:r/2}),g=Object.assign({},i);bi(g,et(a));const u=Object.assign({maxPadding:g,w:n,h:r,x:i.left,y:i.top},i),f=x_(c.concat(l),p);Me(h.fullSize,u,p,f),Me(c,u,p,f),Me(l,u,p,f)&&Me(c,u,p,f),y_(u),Ka(h.leftAndTop,u,p,f),u.x+=u.w,u.y+=u.h,Ka(h.rightAndBottom,u,p,f),s.chartArea={left:u.left,top:u.top,right:u.left+u.w,bottom:u.top+u.h,height:u.h,width:u.w},E(h.chartArea,v=>{const x=v.box;Object.assign(x,s.chartArea),x.update(u.w,u.h,{left:0,top:0,right:0,bottom:0})})}};class wi{acquireContext(t,e){}releaseContext(t){return!1}addEventListener(t,e,a){}removeEventListener(t,e,a){}getDevicePixelRatio(){return 1}getMaximumSize(t,e,a,i){return e=Math.max(0,e||t.width),a=a||t.height,{width:e,height:Math.max(0,i?Math.floor(e/i):a)}}isAttached(t){return!0}updateConfig(t){}}class w_ extends wi{acquireContext(t){return t&&t.getContext&&t.getContext("2d")||null}updateConfig(t){t.options.animation=!1}}const c1="$chartjs",__={touchstart:"mousedown",touchmove:"mousemove",touchend:"mouseup",pointerenter:"mouseenter",pointerdown:"mousedown",pointermove:"mousemove",pointerup:"mouseup",pointerleave:"mouseout",pointerout:"mouseout"},Ja=s=>s===null||s==="";function k_(s,t){const e=s.style,a=s.getAttribute("height"),i=s.getAttribute("width");if(s[c1]={initial:{height:a,width:i,style:{display:e.display,height:e.height,width:e.width}}},e.display=e.display||"block",e.boxSizing=e.boxSizing||"border-box",Ja(i)){const n=Ba(s,"width");n!==void 0&&(s.width=n)}if(Ja(a))if(s.style.height==="")s.height=s.width/(t||2);else{const n=Ba(s,"height");n!==void 0&&(s.height=n)}return s}const _i=Cw?{passive:!0}:!1;function C_(s,t,e){s&&s.addEventListener(t,e,_i)}function S_(s,t,e){s&&s.canvas&&s.canvas.removeEventListener(t,e,_i)}function L_(s,t){const e=__[s.type]||s.type,{x:a,y:i}=It(s,t);return{type:e,chart:t,native:s,x:a!==void 0?a:null,y:i!==void 0?i:null}}function x1(s,t){for(const e of s)if(e===t||e.contains(t))return!0}function A_(s,t,e){const a=s.canvas,i=new MutationObserver(n=>{let r=!1;for(const h of n)r=r||x1(h.addedNodes,a),r=r&&!x1(h.removedNodes,a);r&&e()});return i.observe(document,{childList:!0,subtree:!0}),i}function H_(s,t,e){const a=s.canvas,i=new MutationObserver(n=>{let r=!1;for(const h of n)r=r||x1(h.removedNodes,a),r=r&&!x1(h.addedNodes,a);r&&e()});return i.observe(document,{childList:!0,subtree:!0}),i}const Ee=new Map;let Qa=0;function ki(){const s=window.devicePixelRatio;s!==Qa&&(Qa=s,Ee.forEach((t,e)=>{e.currentDevicePixelRatio!==s&&t()}))}function V_(s,t){Ee.size||window.addEventListener("resize",ki),Ee.set(s,t)}function P_(s){Ee.delete(s),Ee.size||window.removeEventListener("resize",ki)}function D_(s,t,e){const a=s.canvas,i=a&&Ms(a);if(!i)return;const n=Q2((h,c)=>{const l=i.clientWidth;e(h,c),l<i.clientWidth&&e()},window),r=new ResizeObserver(h=>{const c=h[0],l=c.contentRect.width,d=c.contentRect.height;l===0&&d===0||n(l,d)});return r.observe(i),V_(s,n),r}function I1(s,t,e){e&&e.disconnect(),t==="resize"&&P_(s)}function F_(s,t,e){const a=s.canvas,i=Q2(n=>{s.ctx!==null&&e(L_(n,s))},s);return C_(a,t,i),i}class T_ extends wi{acquireContext(t,e){const a=t&&t.getContext&&t.getContext("2d");return a&&a.canvas===t?(k_(t,e),a):null}releaseContext(t){const e=t.canvas;if(!e[c1])return!1;const a=e[c1].initial;["height","width"].forEach(n=>{const r=a[n];F(r)?e.removeAttribute(n):e.setAttribute(n,r)});const i=a.style||{};return Object.keys(i).forEach(n=>{e.style[n]=i[n]}),e.width=e.width,delete e[c1],!0}addEventListener(t,e,a){this.removeEventListener(t,e);const i=t.$proxies||(t.$proxies={}),r={attach:A_,detach:H_,resize:D_}[e]||F_;i[e]=r(t,e,a)}removeEventListener(t,e){const a=t.$proxies||(t.$proxies={}),i=a[e];if(!i)return;({attach:I1,detach:I1,resize:I1}[e]||S_)(t,e,i),a[e]=void 0}getDevicePixelRatio(){return window.devicePixelRatio}getMaximumSize(t,e,a,i){return kw(t,e,a,i)}isAttached(t){const e=t&&Ms(t);return!!(e&&e.isConnected)}}function B_(s){return!ms()||typeof OffscreenCanvas<"u"&&s instanceof OffscreenCanvas?w_:T_}class dt{constructor(){_(this,"x");_(this,"y");_(this,"active",!1);_(this,"options");_(this,"$animations")}tooltipPosition(t){const{x:e,y:a}=this.getProps(["x","y"],t);return{x:e,y:a}}hasValue(){return ae(this.x)&&ae(this.y)}getProps(t,e){const a=this.$animations;if(!e||!a)return this;const i={};return t.forEach(n=>{i[n]=a[n]&&a[n].active()?a[n]._to:this[n]}),i}}_(dt,"defaults",{}),_(dt,"defaultRoutes");function O_(s,t){const e=s.options.ticks,a=E_(s),i=Math.min(e.maxTicksLimit||a,a),n=e.major.enabled?z_(t):[],r=n.length,h=n[0],c=n[r-1],l=[];if(r>i)return I_(t,l,n,r/i),l;const d=R_(n,t,i);if(r>0){let p,g;const u=r>1?Math.round((c-h)/(r-1)):null;for(Ke(t,l,d,F(u)?0:h-u,h),p=0,g=r-1;p<g;p++)Ke(t,l,d,n[p],n[p+1]);return Ke(t,l,d,c,F(u)?t.length:c+u),l}return Ke(t,l,d),l}function E_(s){const t=s.options.offset,e=s._tickSize(),a=s._length/e+(t?0:1),i=s._maxLength/e;return Math.floor(Math.min(a,i))}function R_(s,t,e){const a=$_(s),i=t.length/e;if(!a)return Math.max(i,1);const n=Lb(a);for(let r=0,h=n.length-1;r<h;r++){const c=n[r];if(c>i)return c}return Math.max(i,1)}function z_(s){const t=[];let e,a;for(e=0,a=s.length;e<a;e++)s[e].major&&t.push(e);return t}function I_(s,t,e,a){let i=0,n=e[0],r;for(a=Math.ceil(a),r=0;r<s.length;r++)r===n&&(t.push(s[r]),i++,n=e[i*a])}function Ke(s,t,e,a,i){const n=H(a,0),r=Math.min(H(i,s.length),s.length);let h=0,c,l,d;for(e=Math.ceil(e),i&&(c=i-a,e=c/Math.floor(c/e)),d=n;d<0;)h++,d=Math.round(n+h*e);for(l=Math.max(n,0);l<r;l++)l===d&&(t.push(s[l]),h++,d=Math.round(n+h*e))}function $_(s){const t=s.length;let e,a;if(t<2)return!1;for(a=s[0],e=1;e<t;++e)if(s[e]-s[e-1]!==a)return!1;return a}const Z_=s=>s==="left"?"right":s==="right"?"left":s,t2=(s,t,e)=>t==="top"||t==="left"?s[t]+e:s[t]-e,e2=(s,t)=>Math.min(t||s,s);function s2(s,t){const e=[],a=s.length/t,i=s.length;let n=0;for(;n<i;n+=a)e.push(s[Math.floor(n)]);return e}function W_(s,t,e){const a=s.ticks.length,i=Math.min(t,a-1),n=s._startPixel,r=s._endPixel,h=1e-6;let c=s.getPixelForTick(i),l;if(!(e&&(a===1?l=Math.max(c-n,r-c):t===0?l=(s.getPixelForTick(1)-c)/2:l=(c-s.getPixelForTick(i-1))/2,c+=i<t?l:-l,c<n-h||c>r+h)))return c}function N_(s,t){E(s,e=>{const a=e.gc,i=a.length/2;let n;if(i>t){for(n=0;n<i;++n)delete e.data[a[n]];a.splice(0,i)}})}function ge(s){return s.drawTicks?s.tickLength:0}function a2(s,t){if(!s.display)return 0;const e=G(s.font,t),a=et(s.padding);return(Z(s.text)?s.text.length:1)*e.lineHeight+a.height}function j_(s,t){return Ft(s,{scale:t,type:"scale"})}function U_(s,t,e){return Ft(s,{tick:e,index:t,type:"tick"})}function q_(s,t,e){let a=ps(s);return(e&&t!=="right"||!e&&t==="right")&&(a=Z_(a)),a}function G_(s,t,e,a){const{top:i,left:n,bottom:r,right:h,chart:c}=s,{chartArea:l,scales:d}=c;let p=0,g,u,f;const v=r-i,x=h-n;if(s.isHorizontal()){if(u=J(a,n,h),T(e)){const m=Object.keys(e)[0],M=e[m];f=d[m].getPixelForValue(M)+v-t}else e==="center"?f=(l.bottom+l.top)/2+v-t:f=t2(s,e,t);g=h-n}else{if(T(e)){const m=Object.keys(e)[0],M=e[m];u=d[m].getPixelForValue(M)-x+t}else e==="center"?u=(l.left+l.right)/2-x+t:u=t2(s,e,t);f=J(a,r,i),p=e==="left"?-U:U}return{titleX:u,titleY:f,maxWidth:g,rotation:p}}class Yt extends dt{constructor(t){super(),this.id=t.id,this.type=t.type,this.options=void 0,this.ctx=t.ctx,this.chart=t.chart,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.width=void 0,this.height=void 0,this._margins={left:0,right:0,top:0,bottom:0},this.maxWidth=void 0,this.maxHeight=void 0,this.paddingTop=void 0,this.paddingBottom=void 0,this.paddingLeft=void 0,this.paddingRight=void 0,this.axis=void 0,this.labelRotation=void 0,this.min=void 0,this.max=void 0,this._range=void 0,this.ticks=[],this._gridLineItems=null,this._labelItems=null,this._labelSizes=null,this._length=0,this._maxLength=0,this._longestTextCache={},this._startPixel=void 0,this._endPixel=void 0,this._reversePixels=!1,this._userMax=void 0,this._userMin=void 0,this._suggestedMax=void 0,this._suggestedMin=void 0,this._ticksLength=0,this._borderValue=0,this._cache={},this._dataLimitsCached=!1,this.$context=void 0}init(t){this.options=t.setContext(this.getContext()),this.axis=t.axis,this._userMin=this.parse(t.min),this._userMax=this.parse(t.max),this._suggestedMin=this.parse(t.suggestedMin),this._suggestedMax=this.parse(t.suggestedMax)}parse(t,e){return t}getUserBounds(){let{_userMin:t,_userMax:e,_suggestedMin:a,_suggestedMax:i}=this;return t=ot(t,Number.POSITIVE_INFINITY),e=ot(e,Number.NEGATIVE_INFINITY),a=ot(a,Number.POSITIVE_INFINITY),i=ot(i,Number.NEGATIVE_INFINITY),{min:ot(t,a),max:ot(e,i),minDefined:N(t),maxDefined:N(e)}}getMinMax(t){let{min:e,max:a,minDefined:i,maxDefined:n}=this.getUserBounds(),r;if(i&&n)return{min:e,max:a};const h=this.getMatchingVisibleMetas();for(let c=0,l=h.length;c<l;++c)r=h[c].controller.getMinMax(this,t),i||(e=Math.min(e,r.min)),n||(a=Math.max(a,r.max));return e=n&&e>a?a:e,a=i&&e>a?e:a,{min:ot(e,ot(a,e)),max:ot(a,ot(e,a))}}getPadding(){return{left:this.paddingLeft||0,top:this.paddingTop||0,right:this.paddingRight||0,bottom:this.paddingBottom||0}}getTicks(){return this.ticks}getLabels(){const t=this.chart.data;return this.options.labels||(this.isHorizontal()?t.xLabels:t.yLabels)||t.labels||[]}getLabelItems(t=this.chart.chartArea){return this._labelItems||(this._labelItems=this._computeLabelItems(t))}beforeLayout(){this._cache={},this._dataLimitsCached=!1}beforeUpdate(){z(this.options.beforeUpdate,[this])}update(t,e,a){const{beginAtZero:i,grace:n,ticks:r}=this.options,h=r.sampleSize;this.beforeUpdate(),this.maxWidth=t,this.maxHeight=e,this._margins=a=Object.assign({left:0,right:0,top:0,bottom:0},a),this.ticks=null,this._labelSizes=null,this._gridLineItems=null,this._labelItems=null,this.beforeSetDimensions(),this.setDimensions(),this.afterSetDimensions(),this._maxLength=this.isHorizontal()?this.width+a.left+a.right:this.height+a.top+a.bottom,this._dataLimitsCached||(this.beforeDataLimits(),this.determineDataLimits(),this.afterDataLimits(),this._range=sw(this,n,i),this._dataLimitsCached=!0),this.beforeBuildTicks(),this.ticks=this.buildTicks()||[],this.afterBuildTicks();const c=h<this.ticks.length;this._convertTicksToLabels(c?s2(this.ticks,h):this.ticks),this.configure(),this.beforeCalculateLabelRotation(),this.calculateLabelRotation(),this.afterCalculateLabelRotation(),r.display&&(r.autoSkip||r.source==="auto")&&(this.ticks=O_(this,this.ticks),this._labelSizes=null,this.afterAutoSkip()),c&&this._convertTicksToLabels(this.ticks),this.beforeFit(),this.fit(),this.afterFit(),this.afterUpdate()}configure(){let t=this.options.reverse,e,a;this.isHorizontal()?(e=this.left,a=this.right):(e=this.top,a=this.bottom,t=!t),this._startPixel=e,this._endPixel=a,this._reversePixels=t,this._length=a-e,this._alignToPixels=this.options.alignToPixels}afterUpdate(){z(this.options.afterUpdate,[this])}beforeSetDimensions(){z(this.options.beforeSetDimensions,[this])}setDimensions(){this.isHorizontal()?(this.width=this.maxWidth,this.left=0,this.right=this.width):(this.height=this.maxHeight,this.top=0,this.bottom=this.height),this.paddingLeft=0,this.paddingTop=0,this.paddingRight=0,this.paddingBottom=0}afterSetDimensions(){z(this.options.afterSetDimensions,[this])}_callHooks(t){this.chart.notifyPlugins(t,this.getContext()),z(this.options[t],[this])}beforeDataLimits(){this._callHooks("beforeDataLimits")}determineDataLimits(){}afterDataLimits(){this._callHooks("afterDataLimits")}beforeBuildTicks(){this._callHooks("beforeBuildTicks")}buildTicks(){return[]}afterBuildTicks(){this._callHooks("afterBuildTicks")}beforeTickToLabelConversion(){z(this.options.beforeTickToLabelConversion,[this])}generateTickLabels(t){const e=this.options.ticks;let a,i,n;for(a=0,i=t.length;a<i;a++)n=t[a],n.label=z(e.callback,[n.value,a,t],this)}afterTickToLabelConversion(){z(this.options.afterTickToLabelConversion,[this])}beforeCalculateLabelRotation(){z(this.options.beforeCalculateLabelRotation,[this])}calculateLabelRotation(){const t=this.options,e=t.ticks,a=e2(this.ticks.length,t.ticks.maxTicksLimit),i=e.minRotation||0,n=e.maxRotation;let r=i,h,c,l;if(!this._isVisible()||!e.display||i>=n||a<=1||!this.isHorizontal()){this.labelRotation=i;return}const d=this._getLabelSizes(),p=d.widest.width,g=d.highest.height,u=X(this.chart.width-p,0,this.maxWidth);h=t.offset?this.maxWidth/a:u/(a-1),p+6>h&&(h=u/(a-(t.offset?.5:1)),c=this.maxHeight-ge(t.grid)-e.padding-a2(t.title,this.chart.options.font),l=Math.sqrt(p*p+g*g),r=ls(Math.min(Math.asin(X((d.highest.height+6)/h,-1,1)),Math.asin(X(c/l,-1,1))-Math.asin(X(g/l,-1,1)))),r=Math.max(i,Math.min(n,r))),this.labelRotation=r}afterCalculateLabelRotation(){z(this.options.afterCalculateLabelRotation,[this])}afterAutoSkip(){}beforeFit(){z(this.options.beforeFit,[this])}fit(){const t={width:0,height:0},{chart:e,options:{ticks:a,title:i,grid:n}}=this,r=this._isVisible(),h=this.isHorizontal();if(r){const c=a2(i,e.options.font);if(h?(t.width=this.maxWidth,t.height=ge(n)+c):(t.height=this.maxHeight,t.width=ge(n)+c),a.display&&this.ticks.length){const{first:l,last:d,widest:p,highest:g}=this._getLabelSizes(),u=a.padding*2,f=ct(this.labelRotation),v=Math.cos(f),x=Math.sin(f);if(h){const m=a.mirror?0:x*p.width+v*g.height;t.height=Math.min(this.maxHeight,t.height+m+u)}else{const m=a.mirror?0:v*p.width+x*g.height;t.width=Math.min(this.maxWidth,t.width+m+u)}this._calculatePadding(l,d,x,v)}}this._handleMargins(),h?(this.width=this._length=e.width-this._margins.left-this._margins.right,this.height=t.height):(this.width=t.width,this.height=this._length=e.height-this._margins.top-this._margins.bottom)}_calculatePadding(t,e,a,i){const{ticks:{align:n,padding:r},position:h}=this.options,c=this.labelRotation!==0,l=h!=="top"&&this.axis==="x";if(this.isHorizontal()){const d=this.getPixelForTick(0)-this.left,p=this.right-this.getPixelForTick(this.ticks.length-1);let g=0,u=0;c?l?(g=i*t.width,u=a*e.height):(g=a*t.height,u=i*e.width):n==="start"?u=e.width:n==="end"?g=t.width:n!=="inner"&&(g=t.width/2,u=e.width/2),this.paddingLeft=Math.max((g-d+r)*this.width/(this.width-d),0),this.paddingRight=Math.max((u-p+r)*this.width/(this.width-p),0)}else{let d=e.height/2,p=t.height/2;n==="start"?(d=0,p=t.height):n==="end"&&(d=e.height,p=0),this.paddingTop=d+r,this.paddingBottom=p+r}}_handleMargins(){this._margins&&(this._margins.left=Math.max(this.paddingLeft,this._margins.left),this._margins.top=Math.max(this.paddingTop,this._margins.top),this._margins.right=Math.max(this.paddingRight,this._margins.right),this._margins.bottom=Math.max(this.paddingBottom,this._margins.bottom))}afterFit(){z(this.options.afterFit,[this])}isHorizontal(){const{axis:t,position:e}=this.options;return e==="top"||e==="bottom"||t==="x"}isFullSize(){return this.options.fullSize}_convertTicksToLabels(t){this.beforeTickToLabelConversion(),this.generateTickLabels(t);let e,a;for(e=0,a=t.length;e<a;e++)F(t[e].label)&&(t.splice(e,1),a--,e--);this.afterTickToLabelConversion()}_getLabelSizes(){let t=this._labelSizes;if(!t){const e=this.options.ticks.sampleSize;let a=this.ticks;e<a.length&&(a=s2(a,e)),this._labelSizes=t=this._computeLabelSizes(a,a.length,this.options.ticks.maxTicksLimit)}return t}_computeLabelSizes(t,e,a){const{ctx:i,_longestTextCache:n}=this,r=[],h=[],c=Math.floor(e/e2(e,a));let l=0,d=0,p,g,u,f,v,x,m,M,b,w,y;for(p=0;p<e;p+=c){if(f=t[p].label,v=this._resolveTickFontOptions(p),i.font=x=v.string,m=n[x]=n[x]||{data:{},gc:[]},M=v.lineHeight,b=w=0,!F(f)&&!Z(f))b=f1(i,m.data,m.gc,b,f),w=M;else if(Z(f))for(g=0,u=f.length;g<u;++g)y=f[g],!F(y)&&!Z(y)&&(b=f1(i,m.data,m.gc,b,y),w+=M);r.push(b),h.push(w),l=Math.max(b,l),d=Math.max(w,d)}N_(n,e);const k=r.indexOf(l),C=h.indexOf(d),S=L=>({width:r[L]||0,height:h[L]||0});return{first:S(0),last:S(e-1),widest:S(k),highest:S(C),widths:r,heights:h}}getLabelForValue(t){return t}getPixelForValue(t,e){return NaN}getValueForPixel(t){}getPixelForTick(t){const e=this.ticks;return t<0||t>e.length-1?null:this.getPixelForValue(e[t].value)}getPixelForDecimal(t){this._reversePixels&&(t=1-t);const e=this._startPixel+t*this._length;return Pb(this._alignToPixels?Et(this.chart,e,0):e)}getDecimalForPixel(t){const e=(t-this._startPixel)/this._length;return this._reversePixels?1-e:e}getBasePixel(){return this.getPixelForValue(this.getBaseValue())}getBaseValue(){const{min:t,max:e}=this;return t<0&&e<0?e:t>0&&e>0?t:0}getContext(t){const e=this.ticks||[];if(t>=0&&t<e.length){const a=e[t];return a.$context||(a.$context=U_(this.getContext(),t,a))}return this.$context||(this.$context=j_(this.chart.getContext(),this))}_tickSize(){const t=this.options.ticks,e=ct(this.labelRotation),a=Math.abs(Math.cos(e)),i=Math.abs(Math.sin(e)),n=this._getLabelSizes(),r=t.autoSkipPadding||0,h=n?n.widest.width+r:0,c=n?n.highest.height+r:0;return this.isHorizontal()?c*a>h*i?h/a:c/i:c*i<h*a?c/a:h/i}_isVisible(){const t=this.options.display;return t!=="auto"?!!t:this.getMatchingVisibleMetas().length>0}_computeGridLineItems(t){const e=this.axis,a=this.chart,i=this.options,{grid:n,position:r,border:h}=i,c=n.offset,l=this.isHorizontal(),p=this.ticks.length+(c?1:0),g=ge(n),u=[],f=h.setContext(this.getContext()),v=f.display?f.width:0,x=v/2,m=function($){return Et(a,$,v)};let M,b,w,y,k,C,S,L,P,D,B,Y;if(r==="top")M=m(this.bottom),C=this.bottom-g,L=M-x,D=m(t.top)+x,Y=t.bottom;else if(r==="bottom")M=m(this.top),D=t.top,Y=m(t.bottom)-x,C=M+x,L=this.top+g;else if(r==="left")M=m(this.right),k=this.right-g,S=M-x,P=m(t.left)+x,B=t.right;else if(r==="right")M=m(this.left),P=t.left,B=m(t.right)-x,k=M+x,S=this.left+g;else if(e==="x"){if(r==="center")M=m((t.top+t.bottom)/2+.5);else if(T(r)){const $=Object.keys(r)[0],j=r[$];M=m(this.chart.scales[$].getPixelForValue(j))}D=t.top,Y=t.bottom,C=M+x,L=C+g}else if(e==="y"){if(r==="center")M=m((t.left+t.right)/2);else if(T(r)){const $=Object.keys(r)[0],j=r[$];M=m(this.chart.scales[$].getPixelForValue(j))}k=M-x,S=k-g,P=t.left,B=t.right}const nt=H(i.ticks.maxTicksLimit,p),R=Math.max(1,Math.ceil(p/nt));for(b=0;b<p;b+=R){const $=this.getContext(b),j=n.setContext($),ht=h.setContext($),K=j.lineWidth,Kt=j.color,We=ht.dash||[],Jt=ht.dashOffset,he=j.tickWidth,Tt=j.tickColor,ce=j.tickBorderDash||[],Bt=j.tickBorderDashOffset;w=W_(this,b,c),w!==void 0&&(y=Et(a,w,K),l?k=S=P=B=y:C=L=D=Y=y,u.push({tx1:k,ty1:C,tx2:S,ty2:L,x1:P,y1:D,x2:B,y2:Y,width:K,color:Kt,borderDash:We,borderDashOffset:Jt,tickWidth:he,tickColor:Tt,tickBorderDash:ce,tickBorderDashOffset:Bt}))}return this._ticksLength=p,this._borderValue=M,u}_computeLabelItems(t){const e=this.axis,a=this.options,{position:i,ticks:n}=a,r=this.isHorizontal(),h=this.ticks,{align:c,crossAlign:l,padding:d,mirror:p}=n,g=ge(a.grid),u=g+d,f=p?-d:u,v=-ct(this.labelRotation),x=[];let m,M,b,w,y,k,C,S,L,P,D,B,Y="middle";if(i==="top")k=this.bottom-f,C=this._getXAxisLabelAlignment();else if(i==="bottom")k=this.top+f,C=this._getXAxisLabelAlignment();else if(i==="left"){const R=this._getYAxisLabelAlignment(g);C=R.textAlign,y=R.x}else if(i==="right"){const R=this._getYAxisLabelAlignment(g);C=R.textAlign,y=R.x}else if(e==="x"){if(i==="center")k=(t.top+t.bottom)/2+u;else if(T(i)){const R=Object.keys(i)[0],$=i[R];k=this.chart.scales[R].getPixelForValue($)+u}C=this._getXAxisLabelAlignment()}else if(e==="y"){if(i==="center")y=(t.left+t.right)/2-u;else if(T(i)){const R=Object.keys(i)[0],$=i[R];y=this.chart.scales[R].getPixelForValue($)}C=this._getYAxisLabelAlignment(g).textAlign}e==="y"&&(c==="start"?Y="top":c==="end"&&(Y="bottom"));const nt=this._getLabelSizes();for(m=0,M=h.length;m<M;++m){b=h[m],w=b.label;const R=n.setContext(this.getContext(m));S=this.getPixelForTick(m)+n.labelOffset,L=this._resolveTickFontOptions(m),P=L.lineHeight,D=Z(w)?w.length:1;const $=D/2,j=R.color,ht=R.textStrokeColor,K=R.textStrokeWidth;let Kt=C;r?(y=S,C==="inner"&&(m===M-1?Kt=this.options.reverse?"left":"right":m===0?Kt=this.options.reverse?"right":"left":Kt="center"),i==="top"?l==="near"||v!==0?B=-D*P+P/2:l==="center"?B=-nt.highest.height/2-$*P+P:B=-nt.highest.height+P/2:l==="near"||v!==0?B=P/2:l==="center"?B=nt.highest.height/2-$*P:B=nt.highest.height-D*P,p&&(B*=-1),v!==0&&!R.showLabelBackdrop&&(y+=P/2*Math.sin(v))):(k=S,B=(1-D)*P/2);let We;if(R.showLabelBackdrop){const Jt=et(R.backdropPadding),he=nt.heights[m],Tt=nt.widths[m];let ce=B-Jt.top,Bt=0-Jt.left;switch(Y){case"middle":ce-=he/2;break;case"bottom":ce-=he;break}switch(C){case"center":Bt-=Tt/2;break;case"right":Bt-=Tt;break;case"inner":m===M-1?Bt-=Tt:m>0&&(Bt-=Tt/2);break}We={left:Bt,top:ce,width:Tt+Jt.width,height:he+Jt.height,color:R.backdropColor}}x.push({label:w,font:L,textOffset:B,options:{rotation:v,color:j,strokeColor:ht,strokeWidth:K,textAlign:Kt,textBaseline:Y,translation:[y,k],backdrop:We}})}return x}_getXAxisLabelAlignment(){const{position:t,ticks:e}=this.options;if(-ct(this.labelRotation))return t==="top"?"left":"right";let i="center";return e.align==="start"?i="left":e.align==="end"?i="right":e.align==="inner"&&(i="inner"),i}_getYAxisLabelAlignment(t){const{position:e,ticks:{crossAlign:a,mirror:i,padding:n}}=this.options,r=this._getLabelSizes(),h=t+n,c=r.widest.width;let l,d;return e==="left"?i?(d=this.right+n,a==="near"?l="left":a==="center"?(l="center",d+=c/2):(l="right",d+=c)):(d=this.right-h,a==="near"?l="right":a==="center"?(l="center",d-=c/2):(l="left",d=this.left)):e==="right"?i?(d=this.left+n,a==="near"?l="right":a==="center"?(l="center",d-=c/2):(l="left",d-=c)):(d=this.left+h,a==="near"?l="left":a==="center"?(l="center",d+=c/2):(l="right",d=this.right)):l="right",{textAlign:l,x:d}}_computeLabelArea(){if(this.options.ticks.mirror)return;const t=this.chart,e=this.options.position;if(e==="left"||e==="right")return{top:0,left:this.left,bottom:t.height,right:this.right};if(e==="top"||e==="bottom")return{top:this.top,left:0,bottom:this.bottom,right:t.width}}drawBackground(){const{ctx:t,options:{backgroundColor:e},left:a,top:i,width:n,height:r}=this;e&&(t.save(),t.fillStyle=e,t.fillRect(a,i,n,r),t.restore())}getLineWidthForValue(t){const e=this.options.grid;if(!this._isVisible()||!e.display)return 0;const i=this.ticks.findIndex(n=>n.value===t);return i>=0?e.setContext(this.getContext(i)).lineWidth:0}drawGrid(t){const e=this.options.grid,a=this.ctx,i=this._gridLineItems||(this._gridLineItems=this._computeGridLineItems(t));let n,r;const h=(c,l,d)=>{!d.width||!d.color||(a.save(),a.lineWidth=d.width,a.strokeStyle=d.color,a.setLineDash(d.borderDash||[]),a.lineDashOffset=d.borderDashOffset,a.beginPath(),a.moveTo(c.x,c.y),a.lineTo(l.x,l.y),a.stroke(),a.restore())};if(e.display)for(n=0,r=i.length;n<r;++n){const c=i[n];e.drawOnChartArea&&h({x:c.x1,y:c.y1},{x:c.x2,y:c.y2},c),e.drawTicks&&h({x:c.tx1,y:c.ty1},{x:c.tx2,y:c.ty2},{color:c.tickColor,width:c.tickWidth,borderDash:c.tickBorderDash,borderDashOffset:c.tickBorderDashOffset})}}drawBorder(){const{chart:t,ctx:e,options:{border:a,grid:i}}=this,n=a.setContext(this.getContext()),r=a.display?n.width:0;if(!r)return;const h=i.setContext(this.getContext(0)).lineWidth,c=this._borderValue;let l,d,p,g;this.isHorizontal()?(l=Et(t,this.left,r)-r/2,d=Et(t,this.right,h)+h/2,p=g=c):(p=Et(t,this.top,r)-r/2,g=Et(t,this.bottom,h)+h/2,l=d=c),e.save(),e.lineWidth=n.width,e.strokeStyle=n.color,e.beginPath(),e.moveTo(l,p),e.lineTo(d,g),e.stroke(),e.restore()}drawLabels(t){if(!this.options.ticks.display)return;const a=this.ctx,i=this._computeLabelArea();i&&_1(a,i);const n=this.getLabelItems(t);for(const r of n){const h=r.options,c=r.font,l=r.label,d=r.textOffset;Xt(a,l,0,d,c,h)}i&&k1(a)}drawTitle(){const{ctx:t,options:{position:e,title:a,reverse:i}}=this;if(!a.display)return;const n=G(a.font),r=et(a.padding),h=a.align;let c=n.lineHeight/2;e==="bottom"||e==="center"||T(e)?(c+=r.bottom,Z(a.text)&&(c+=n.lineHeight*(a.text.length-1))):c+=r.top;const{titleX:l,titleY:d,maxWidth:p,rotation:g}=G_(this,c,e,h);Xt(t,a.text,0,0,n,{color:a.color,maxWidth:p,rotation:g,textAlign:q_(h,e,i),textBaseline:"middle",translation:[l,d]})}draw(t){this._isVisible()&&(this.drawBackground(),this.drawGrid(t),this.drawBorder(),this.drawTitle(),this.drawLabels(t))}_layers(){const t=this.options,e=t.ticks&&t.ticks.z||0,a=H(t.grid&&t.grid.z,-1),i=H(t.border&&t.border.z,0);return!this._isVisible()||this.draw!==Yt.prototype.draw?[{z:e,draw:n=>{this.draw(n)}}]:[{z:a,draw:n=>{this.drawBackground(),this.drawGrid(n),this.drawTitle()}},{z:i,draw:()=>{this.drawBorder()}},{z:e,draw:n=>{this.drawLabels(n)}}]}getMatchingVisibleMetas(t){const e=this.chart.getSortedVisibleDatasetMetas(),a=this.axis+"AxisID",i=[];let n,r;for(n=0,r=e.length;n<r;++n){const h=e[n];h[a]===this.id&&(!t||h.type===t)&&i.push(h)}return i}_resolveTickFontOptions(t){const e=this.options.ticks.setContext(this.getContext(t));return G(e.font)}_maxDigits(){const t=this._resolveTickFontOptions(0).lineHeight;return(this.isHorizontal()?this.width:this.height)/t}}class Je{constructor(t,e,a){this.type=t,this.scope=e,this.override=a,this.items=Object.create(null)}isForType(t){return Object.prototype.isPrototypeOf.call(this.type.prototype,t.prototype)}register(t){const e=Object.getPrototypeOf(t);let a;K_(e)&&(a=this.register(e));const i=this.items,n=t.id,r=this.scope+"."+n;if(!n)throw new Error("class does not have id: "+t);return n in i||(i[n]=t,X_(t,r,a),this.override&&W.override(t.id,t.overrides)),r}get(t){return this.items[t]}unregister(t){const e=this.items,a=t.id,i=this.scope;a in e&&delete e[a],i&&a in W[i]&&(delete W[i][a],this.override&&delete Gt[a])}}function X_(s,t,e){const a=Fe(Object.create(null),[e?W.get(e):{},W.get(t),s.defaults]);W.set(t,a),s.defaultRoutes&&Y_(t,s.defaultRoutes),s.descriptors&&W.describe(t,s.descriptors)}function Y_(s,t){Object.keys(t).forEach(e=>{const a=e.split("."),i=a.pop(),n=[s].concat(a).join("."),r=t[e].split("."),h=r.pop(),c=r.join(".");W.route(n,i,c,h)})}function K_(s){return"id"in s&&"defaults"in s}class J_{constructor(){this.controllers=new Je(lt,"datasets",!0),this.elements=new Je(dt,"elements"),this.plugins=new Je(Object,"plugins"),this.scales=new Je(Yt,"scales"),this._typedRegistries=[this.controllers,this.scales,this.elements]}add(...t){this._each("register",t)}remove(...t){this._each("unregister",t)}addControllers(...t){this._each("register",t,this.controllers)}addElements(...t){this._each("register",t,this.elements)}addPlugins(...t){this._each("register",t,this.plugins)}addScales(...t){this._each("register",t,this.scales)}getController(t){return this._get(t,this.controllers,"controller")}getElement(t){return this._get(t,this.elements,"element")}getPlugin(t){return this._get(t,this.plugins,"plugin")}getScale(t){return this._get(t,this.scales,"scale")}removeControllers(...t){this._each("unregister",t,this.controllers)}removeElements(...t){this._each("unregister",t,this.elements)}removePlugins(...t){this._each("unregister",t,this.plugins)}removeScales(...t){this._each("unregister",t,this.scales)}_each(t,e,a){[...e].forEach(i=>{const n=a||this._getRegistryForType(i);a||n.isForType(i)||n===this.plugins&&i.id?this._exec(t,n,i):E(i,r=>{const h=a||this._getRegistryForType(r);this._exec(t,h,r)})})}_exec(t,e,a){const i=cs(t);z(a["before"+i],[],a),e[t](a),z(a["after"+i],[],a)}_getRegistryForType(t){for(let e=0;e<this._typedRegistries.length;e++){const a=this._typedRegistries[e];if(a.isForType(t))return a}return this.plugins}_get(t,e,a){const i=e.get(t);if(i===void 0)throw new Error('"'+t+'" is not a registered '+a+".");return i}}var vt=new J_;class Q_{constructor(){this._init=void 0}notify(t,e,a,i){if(e==="beforeInit"&&(this._init=this._createDescriptors(t,!0),this._notify(this._init,t,"install")),this._init===void 0)return;const n=i?this._descriptors(t).filter(i):this._descriptors(t),r=this._notify(n,t,e,a);return e==="afterDestroy"&&(this._notify(n,t,"stop"),this._notify(this._init,t,"uninstall"),this._init=void 0),r}_notify(t,e,a,i){i=i||{};for(const n of t){const r=n.plugin,h=r[a],c=[e,i,n.options];if(z(h,c,r)===!1&&i.cancelable)return!1}return!0}invalidate(){F(this._cache)||(this._oldCache=this._cache,this._cache=void 0)}_descriptors(t){if(this._cache)return this._cache;const e=this._cache=this._createDescriptors(t);return this._notifyStateChanges(t),e}_createDescriptors(t,e){const a=t&&t.config,i=H(a.options&&a.options.plugins,{}),n=tk(a);return i===!1&&!e?[]:sk(t,n,i,e)}_notifyStateChanges(t){const e=this._oldCache||[],a=this._cache,i=(n,r)=>n.filter(h=>!r.some(c=>h.plugin.id===c.plugin.id));this._notify(i(e,a),t,"stop"),this._notify(i(a,e),t,"start")}}function tk(s){const t={},e=[],a=Object.keys(vt.plugins.items);for(let n=0;n<a.length;n++)e.push(vt.getPlugin(a[n]));const i=s.plugins||[];for(let n=0;n<i.length;n++){const r=i[n];e.indexOf(r)===-1&&(e.push(r),t[r.id]=!0)}return{plugins:e,localIds:t}}function ek(s,t){return!t&&s===!1?null:s===!0?{}:s}function sk(s,{plugins:t,localIds:e},a,i){const n=[],r=s.getContext();for(const h of t){const c=h.id,l=ek(a[c],i);l!==null&&n.push({plugin:h,options:ak(s.config,{plugin:h,local:e[c]},l,r)})}return n}function ak(s,{plugin:t,local:e},a,i){const n=s.pluginScopeKeys(t),r=s.getOptionScopes(a,n);return e&&t.defaults&&r.push(t.defaults),s.createResolver(r,i,[""],{scriptable:!1,indexable:!1,allKeys:!0})}function K1(s,t){const e=W.datasets[s]||{};return((t.datasets||{})[s]||{}).indexAxis||t.indexAxis||e.indexAxis||"x"}function ik(s,t){let e=s;return s==="_index_"?e=t:s==="_value_"&&(e=t==="x"?"y":"x"),e}function nk(s,t){return s===t?"_index_":"_value_"}function i2(s){if(s==="x"||s==="y"||s==="r")return s}function ok(s){if(s==="top"||s==="bottom")return"x";if(s==="left"||s==="right")return"y"}function J1(s,...t){if(i2(s))return s;for(const e of t){const a=e.axis||ok(e.position)||s.length>1&&i2(s[0].toLowerCase());if(a)return a}throw new Error(`Cannot determine type of '${s}' axis. Please provide 'axis' or 'position' option.`)}function n2(s,t,e){if(e[t+"AxisID"]===s)return{axis:t}}function rk(s,t){if(t.data&&t.data.datasets){const e=t.data.datasets.filter(a=>a.xAxisID===s||a.yAxisID===s);if(e.length)return n2(s,"x",e[0])||n2(s,"y",e[0])}return{}}function hk(s,t){const e=Gt[s.type]||{scales:{}},a=t.scales||{},i=K1(s.type,t),n=Object.create(null);return Object.keys(a).forEach(r=>{const h=a[r];if(!T(h))return console.error(`Invalid scale configuration for scale: ${r}`);if(h._proxy)return console.warn(`Ignoring resolver passed as options for scale: ${r}`);const c=J1(r,h,rk(r,s),W.scales[h.type]),l=nk(c,i),d=e.scales||{};n[r]=ke(Object.create(null),[{axis:c},h,d[c],d[l]])}),s.data.datasets.forEach(r=>{const h=r.type||s.type,c=r.indexAxis||K1(h,t),d=(Gt[h]||{}).scales||{};Object.keys(d).forEach(p=>{const g=ik(p,c),u=r[g+"AxisID"]||g;n[u]=n[u]||Object.create(null),ke(n[u],[{axis:g},a[u],d[p]])})}),Object.keys(n).forEach(r=>{const h=n[r];ke(h,[W.scales[h.type],W.scale])}),n}function Ci(s){const t=s.options||(s.options={});t.plugins=H(t.plugins,{}),t.scales=hk(s,t)}function Si(s){return s=s||{},s.datasets=s.datasets||[],s.labels=s.labels||[],s}function ck(s){return s=s||{},s.data=Si(s.data),Ci(s),s}const o2=new Map,Li=new Set;function Qe(s,t){let e=o2.get(s);return e||(e=t(),o2.set(s,e),Li.add(e)),e}const ue=(s,t,e)=>{const a=Pt(t,e);a!==void 0&&s.add(a)};class lk{constructor(t){this._config=ck(t),this._scopeCache=new Map,this._resolverCache=new Map}get platform(){return this._config.platform}get type(){return this._config.type}set type(t){this._config.type=t}get data(){return this._config.data}set data(t){this._config.data=Si(t)}get options(){return this._config.options}set options(t){this._config.options=t}get plugins(){return this._config.plugins}update(){const t=this._config;this.clearCache(),Ci(t)}clearCache(){this._scopeCache.clear(),this._resolverCache.clear()}datasetScopeKeys(t){return Qe(t,()=>[[`datasets.${t}`,""]])}datasetAnimationScopeKeys(t,e){return Qe(`${t}.transition.${e}`,()=>[[`datasets.${t}.transitions.${e}`,`transitions.${e}`],[`datasets.${t}`,""]])}datasetElementScopeKeys(t,e){return Qe(`${t}-${e}`,()=>[[`datasets.${t}.elements.${e}`,`datasets.${t}`,`elements.${e}`,""]])}pluginScopeKeys(t){const e=t.id,a=this.type;return Qe(`${a}-plugin-${e}`,()=>[[`plugins.${e}`,...t.additionalOptionScopes||[]]])}_cachedScopes(t,e){const a=this._scopeCache;let i=a.get(t);return(!i||e)&&(i=new Map,a.set(t,i)),i}getOptionScopes(t,e,a){const{options:i,type:n}=this,r=this._cachedScopes(t,a),h=r.get(e);if(h)return h;const c=new Set;e.forEach(d=>{t&&(c.add(t),d.forEach(p=>ue(c,t,p))),d.forEach(p=>ue(c,i,p)),d.forEach(p=>ue(c,Gt[n]||{},p)),d.forEach(p=>ue(c,W,p)),d.forEach(p=>ue(c,G1,p))});const l=Array.from(c);return l.length===0&&l.push(Object.create(null)),Li.has(e)&&r.set(e,l),l}chartOptionScopes(){const{options:t,type:e}=this;return[t,Gt[e]||{},W.datasets[e]||{},{type:e},W,G1]}resolveNamedOptions(t,e,a,i=[""]){const n={$shared:!0},{resolver:r,subPrefixes:h}=r2(this._resolverCache,t,i);let c=r;if(pk(r,e)){n.$shared=!1,a=Dt(a)?a():a;const l=this.createResolver(t,a,h);c=ie(r,a,l)}for(const l of e)n[l]=c[l];return n}createResolver(t,e,a=[""],i){const{resolver:n}=r2(this._resolverCache,t,a);return T(e)?ie(n,e,void 0,i):n}}function r2(s,t,e){let a=s.get(t);a||(a=new Map,s.set(t,a));const i=e.join();let n=a.get(i);return n||(n={resolver:fs(t,e),subPrefixes:e.filter(h=>!h.toLowerCase().includes("hover"))},a.set(i,n)),n}const dk=s=>T(s)&&Object.getOwnPropertyNames(s).some(t=>Dt(s[t]));function pk(s,t){const{isScriptable:e,isIndexable:a}=ni(s);for(const i of t){const n=e(i),r=a(i),h=(r||n)&&s[i];if(n&&(Dt(h)||dk(h))||r&&Z(h))return!0}return!1}var gk="4.5.1";const uk=["top","bottom","left","right","chartArea"];function h2(s,t){return s==="top"||s==="bottom"||uk.indexOf(s)===-1&&t==="x"}function c2(s,t){return function(e,a){return e[s]===a[s]?e[t]-a[t]:e[s]-a[s]}}function l2(s){const t=s.chart,e=t.options.animation;t.notifyPlugins("afterRender"),z(e&&e.onComplete,[s],t)}function fk(s){const t=s.chart,e=t.options.animation;z(e&&e.onProgress,[s],t)}function Ai(s){return ms()&&typeof s=="string"?s=document.getElementById(s):s&&s.length&&(s=s[0]),s&&s.canvas&&(s=s.canvas),s}const l1={},d2=s=>{const t=Ai(s);return Object.values(l1).filter(e=>e.canvas===t).pop()};function vk(s,t,e){const a=Object.keys(s);for(const i of a){const n=+i;if(n>=t){const r=s[i];delete s[i],(e>0||n>t)&&(s[n+e]=r)}}}function xk(s,t,e,a){return!e||s.type==="mouseout"?null:a?t:s}class at{static register(...t){vt.add(...t),p2()}static unregister(...t){vt.remove(...t),p2()}constructor(t,e){const a=this.config=new lk(e),i=Ai(t),n=d2(i);if(n)throw new Error("Canvas is already in use. Chart with ID '"+n.id+"' must be destroyed before the canvas with ID '"+n.canvas.id+"' can be reused.");const r=a.createResolver(a.chartOptionScopes(),this.getContext());this.platform=new(a.platform||B_(i)),this.platform.updateConfig(a);const h=this.platform.acquireContext(i,r.aspectRatio),c=h&&h.canvas,l=c&&c.height,d=c&&c.width;if(this.id=mb(),this.ctx=h,this.canvas=c,this.width=d,this.height=l,this._options=r,this._aspectRatio=this.aspectRatio,this._layers=[],this._metasets=[],this._stacks=void 0,this.boxes=[],this.currentDevicePixelRatio=void 0,this.chartArea=void 0,this._active=[],this._lastEvent=void 0,this._listeners={},this._responsiveListeners=void 0,this._sortedMetasets=[],this.scales={},this._plugins=new Q_,this.$proxies={},this._hiddenIndices={},this.attached=!1,this._animationsDisabled=void 0,this.$context=void 0,this._doResize=Bb(p=>this.update(p),r.resizeDelay||0),this._dataChanges=[],l1[this.id]=this,!h||!c){console.error("Failed to create chart: can't acquire context from the given item");return}Mt.listen(this,"complete",l2),Mt.listen(this,"progress",fk),this._initialize(),this.attached&&this.update()}get aspectRatio(){const{options:{aspectRatio:t,maintainAspectRatio:e},width:a,height:i,_aspectRatio:n}=this;return F(t)?e&&n?n:i?a/i:null:t}get data(){return this.config.data}set data(t){this.config.data=t}get options(){return this._options}set options(t){this.config.options=t}get registry(){return vt}_initialize(){return this.notifyPlugins("beforeInit"),this.options.responsive?this.resize():Ta(this,this.options.devicePixelRatio),this.bindEvents(),this.notifyPlugins("afterInit"),this}clear(){return Pa(this.canvas,this.ctx),this}stop(){return Mt.stop(this),this}resize(t,e){Mt.running(this)?this._resizeBeforeDraw={width:t,height:e}:this._resize(t,e)}_resize(t,e){const a=this.options,i=this.canvas,n=a.maintainAspectRatio&&this.aspectRatio,r=this.platform.getMaximumSize(i,t,e,n),h=a.devicePixelRatio||this.platform.getDevicePixelRatio(),c=this.width?"resize":"attach";this.width=r.width,this.height=r.height,this._aspectRatio=this.aspectRatio,Ta(this,h,!0)&&(this.notifyPlugins("resize",{size:r}),z(a.onResize,[this,r],this),this.attached&&this._doResize(c)&&this.render())}ensureScalesHaveIDs(){const e=this.options.scales||{};E(e,(a,i)=>{a.id=i})}buildOrUpdateScales(){const t=this.options,e=t.scales,a=this.scales,i=Object.keys(a).reduce((r,h)=>(r[h]=!1,r),{});let n=[];e&&(n=n.concat(Object.keys(e).map(r=>{const h=e[r],c=J1(r,h),l=c==="r",d=c==="x";return{options:h,dposition:l?"chartArea":d?"bottom":"left",dtype:l?"radialLinear":d?"category":"linear"}}))),E(n,r=>{const h=r.options,c=h.id,l=J1(c,h),d=H(h.type,r.dtype);(h.position===void 0||h2(h.position,l)!==h2(r.dposition))&&(h.position=r.dposition),i[c]=!0;let p=null;if(c in a&&a[c].type===d)p=a[c];else{const g=vt.getScale(d);p=new g({id:c,type:d,ctx:this.ctx,chart:this}),a[p.id]=p}p.init(h,t)}),E(i,(r,h)=>{r||delete a[h]}),E(a,r=>{tt.configure(this,r,r.options),tt.addBox(this,r)})}_updateMetasets(){const t=this._metasets,e=this.data.datasets.length,a=t.length;if(t.sort((i,n)=>i.index-n.index),a>e){for(let i=e;i<a;++i)this._destroyDatasetMeta(i);t.splice(e,a-e)}this._sortedMetasets=t.slice(0).sort(c2("order","index"))}_removeUnreferencedMetasets(){const{_metasets:t,data:{datasets:e}}=this;t.length>e.length&&delete this._stacks,t.forEach((a,i)=>{e.filter(n=>n===a._dataset).length===0&&this._destroyDatasetMeta(i)})}buildOrUpdateControllers(){const t=[],e=this.data.datasets;let a,i;for(this._removeUnreferencedMetasets(),a=0,i=e.length;a<i;a++){const n=e[a];let r=this.getDatasetMeta(a);const h=n.type||this.config.type;if(r.type&&r.type!==h&&(this._destroyDatasetMeta(a),r=this.getDatasetMeta(a)),r.type=h,r.indexAxis=n.indexAxis||K1(h,this.options),r.order=n.order||0,r.index=a,r.label=""+n.label,r.visible=this.isDatasetVisible(a),r.controller)r.controller.updateIndex(a),r.controller.linkScales();else{const c=vt.getController(h),{datasetElementType:l,dataElementType:d}=W.datasets[h];Object.assign(c,{dataElementType:vt.getElement(d),datasetElementType:l&&vt.getElement(l)}),r.controller=new c(this,a),t.push(r.controller)}}return this._updateMetasets(),t}_resetElements(){E(this.data.datasets,(t,e)=>{this.getDatasetMeta(e).controller.reset()},this)}reset(){this._resetElements(),this.notifyPlugins("reset")}update(t){const e=this.config;e.update();const a=this._options=e.createResolver(e.chartOptionScopes(),this.getContext()),i=this._animationsDisabled=!a.animation;if(this._updateScales(),this._checkEventBindings(),this._updateHiddenIndices(),this._plugins.invalidate(),this.notifyPlugins("beforeUpdate",{mode:t,cancelable:!0})===!1)return;const n=this.buildOrUpdateControllers();this.notifyPlugins("beforeElementsUpdate");let r=0;for(let l=0,d=this.data.datasets.length;l<d;l++){const{controller:p}=this.getDatasetMeta(l),g=!i&&n.indexOf(p)===-1;p.buildOrUpdateElements(g),r=Math.max(+p.getMaxOverflow(),r)}r=this._minPadding=a.layout.autoPadding?r:0,this._updateLayout(r),i||E(n,l=>{l.reset()}),this._updateDatasets(t),this.notifyPlugins("afterUpdate",{mode:t}),this._layers.sort(c2("z","_idx"));const{_active:h,_lastEvent:c}=this;c?this._eventHandler(c,!0):h.length&&this._updateHoverStyles(h,h,!0),this.render()}_updateScales(){E(this.scales,t=>{tt.removeBox(this,t)}),this.ensureScalesHaveIDs(),this.buildOrUpdateScales()}_checkEventBindings(){const t=this.options,e=new Set(Object.keys(this._listeners)),a=new Set(t.events);(!wa(e,a)||!!this._responsiveListeners!==t.responsive)&&(this.unbindEvents(),this.bindEvents())}_updateHiddenIndices(){const{_hiddenIndices:t}=this,e=this._getUniformDataChanges()||[];for(const{method:a,start:i,count:n}of e){const r=a==="_removeElements"?-n:n;vk(t,i,r)}}_getUniformDataChanges(){const t=this._dataChanges;if(!t||!t.length)return;this._dataChanges=[];const e=this.data.datasets.length,a=n=>new Set(t.filter(r=>r[0]===n).map((r,h)=>h+","+r.splice(1).join(","))),i=a(0);for(let n=1;n<e;n++)if(!wa(i,a(n)))return;return Array.from(i).map(n=>n.split(",")).map(n=>({method:n[1],start:+n[2],count:+n[3]}))}_updateLayout(t){if(this.notifyPlugins("beforeLayout",{cancelable:!0})===!1)return;tt.update(this,this.width,this.height,t);const e=this.chartArea,a=e.width<=0||e.height<=0;this._layers=[],E(this.boxes,i=>{a&&i.position==="chartArea"||(i.configure&&i.configure(),this._layers.push(...i._layers()))},this),this._layers.forEach((i,n)=>{i._idx=n}),this.notifyPlugins("afterLayout")}_updateDatasets(t){if(this.notifyPlugins("beforeDatasetsUpdate",{mode:t,cancelable:!0})!==!1){for(let e=0,a=this.data.datasets.length;e<a;++e)this.getDatasetMeta(e).controller.configure();for(let e=0,a=this.data.datasets.length;e<a;++e)this._updateDataset(e,Dt(t)?t({datasetIndex:e}):t);this.notifyPlugins("afterDatasetsUpdate",{mode:t})}}_updateDataset(t,e){const a=this.getDatasetMeta(t),i={meta:a,index:t,mode:e,cancelable:!0};this.notifyPlugins("beforeDatasetUpdate",i)!==!1&&(a.controller._update(e),i.cancelable=!1,this.notifyPlugins("afterDatasetUpdate",i))}render(){this.notifyPlugins("beforeRender",{cancelable:!0})!==!1&&(Mt.has(this)?this.attached&&!Mt.running(this)&&Mt.start(this):(this.draw(),l2({chart:this})))}draw(){let t;if(this._resizeBeforeDraw){const{width:a,height:i}=this._resizeBeforeDraw;this._resizeBeforeDraw=null,this._resize(a,i)}if(this.clear(),this.width<=0||this.height<=0||this.notifyPlugins("beforeDraw",{cancelable:!0})===!1)return;const e=this._layers;for(t=0;t<e.length&&e[t].z<=0;++t)e[t].draw(this.chartArea);for(this._drawDatasets();t<e.length;++t)e[t].draw(this.chartArea);this.notifyPlugins("afterDraw")}_getSortedDatasetMetas(t){const e=this._sortedMetasets,a=[];let i,n;for(i=0,n=e.length;i<n;++i){const r=e[i];(!t||r.visible)&&a.push(r)}return a}getSortedVisibleDatasetMetas(){return this._getSortedDatasetMetas(!0)}_drawDatasets(){if(this.notifyPlugins("beforeDatasetsDraw",{cancelable:!0})===!1)return;const t=this.getSortedVisibleDatasetMetas();for(let e=t.length-1;e>=0;--e)this._drawDataset(t[e]);this.notifyPlugins("afterDatasetsDraw")}_drawDataset(t){const e=this.ctx,a={meta:t,index:t.index,cancelable:!0},i=vi(this,t);this.notifyPlugins("beforeDatasetDraw",a)!==!1&&(i&&_1(e,i),t.controller.draw(),i&&k1(e),a.cancelable=!1,this.notifyPlugins("afterDatasetDraw",a))}isPointInArea(t){return kt(t,this.chartArea,this._minPadding)}getElementsAtEventForMode(t,e,a,i){const n=u_.modes[e];return typeof n=="function"?n(this,t,a,i):[]}getDatasetMeta(t){const e=this.data.datasets[t],a=this._metasets;let i=a.filter(n=>n&&n._dataset===e).pop();return i||(i={type:null,data:[],dataset:null,controller:null,hidden:null,xAxisID:null,yAxisID:null,order:e&&e.order||0,index:t,_dataset:e,_parsed:[],_sorted:!1},a.push(i)),i}getContext(){return this.$context||(this.$context=Ft(null,{chart:this,type:"chart"}))}getVisibleDatasetCount(){return this.getSortedVisibleDatasetMetas().length}isDatasetVisible(t){const e=this.data.datasets[t];if(!e)return!1;const a=this.getDatasetMeta(t);return typeof a.hidden=="boolean"?!a.hidden:!e.hidden}setDatasetVisibility(t,e){const a=this.getDatasetMeta(t);a.hidden=!e}toggleDataVisibility(t){this._hiddenIndices[t]=!this._hiddenIndices[t]}getDataVisibility(t){return!this._hiddenIndices[t]}_updateVisibility(t,e,a){const i=a?"show":"hide",n=this.getDatasetMeta(t),r=n.controller._resolveAnimations(void 0,i);Te(e)?(n.data[e].hidden=!a,this.update()):(this.setDatasetVisibility(t,a),r.update(n,{visible:a}),this.update(h=>h.datasetIndex===t?i:void 0))}hide(t,e){this._updateVisibility(t,e,!1)}show(t,e){this._updateVisibility(t,e,!0)}_destroyDatasetMeta(t){const e=this._metasets[t];e&&e.controller&&e.controller._destroy(),delete this._metasets[t]}_stop(){let t,e;for(this.stop(),Mt.remove(this),t=0,e=this.data.datasets.length;t<e;++t)this._destroyDatasetMeta(t)}destroy(){this.notifyPlugins("beforeDestroy");const{canvas:t,ctx:e}=this;this._stop(),this.config.clearCache(),t&&(this.unbindEvents(),Pa(t,e),this.platform.releaseContext(e),this.canvas=null,this.ctx=null),delete l1[this.id],this.notifyPlugins("afterDestroy")}toBase64Image(...t){return this.canvas.toDataURL(...t)}bindEvents(){this.bindUserEvents(),this.options.responsive?this.bindResponsiveEvents():this.attached=!0}bindUserEvents(){const t=this._listeners,e=this.platform,a=(n,r)=>{e.addEventListener(this,n,r),t[n]=r},i=(n,r,h)=>{n.offsetX=r,n.offsetY=h,this._eventHandler(n)};E(this.options.events,n=>a(n,i))}bindResponsiveEvents(){this._responsiveListeners||(this._responsiveListeners={});const t=this._responsiveListeners,e=this.platform,a=(c,l)=>{e.addEventListener(this,c,l),t[c]=l},i=(c,l)=>{t[c]&&(e.removeEventListener(this,c,l),delete t[c])},n=(c,l)=>{this.canvas&&this.resize(c,l)};let r;const h=()=>{i("attach",h),this.attached=!0,this.resize(),a("resize",n),a("detach",r)};r=()=>{this.attached=!1,i("resize",n),this._stop(),this._resize(0,0),a("attach",h)},e.isAttached(this.canvas)?h():r()}unbindEvents(){E(this._listeners,(t,e)=>{this.platform.removeEventListener(this,e,t)}),this._listeners={},E(this._responsiveListeners,(t,e)=>{this.platform.removeEventListener(this,e,t)}),this._responsiveListeners=void 0}updateHoverStyle(t,e,a){const i=a?"set":"remove";let n,r,h,c;for(e==="dataset"&&(n=this.getDatasetMeta(t[0].datasetIndex),n.controller["_"+i+"DatasetHoverStyle"]()),h=0,c=t.length;h<c;++h){r=t[h];const l=r&&this.getDatasetMeta(r.datasetIndex).controller;l&&l[i+"HoverStyle"](r.element,r.datasetIndex,r.index)}}getActiveElements(){return this._active||[]}setActiveElements(t){const e=this._active||[],a=t.map(({datasetIndex:n,index:r})=>{const h=this.getDatasetMeta(n);if(!h)throw new Error("No dataset found at index "+n);return{datasetIndex:n,element:h.data[r],index:r}});!p1(a,e)&&(this._active=a,this._lastEvent=null,this._updateHoverStyles(a,e))}notifyPlugins(t,e,a){return this._plugins.notify(this,t,e,a)}isPluginEnabled(t){return this._plugins._cache.filter(e=>e.plugin.id===t).length===1}_updateHoverStyles(t,e,a){const i=this.options.hover,n=(c,l)=>c.filter(d=>!l.some(p=>d.datasetIndex===p.datasetIndex&&d.index===p.index)),r=n(e,t),h=a?t:n(t,e);r.length&&this.updateHoverStyle(r,i.mode,!1),h.length&&i.mode&&this.updateHoverStyle(h,i.mode,!0)}_eventHandler(t,e){const a={event:t,replay:e,cancelable:!0,inChartArea:this.isPointInArea(t)},i=r=>(r.options.events||this.options.events).includes(t.native.type);if(this.notifyPlugins("beforeEvent",a,i)===!1)return;const n=this._handleEvent(t,e,a.inChartArea);return a.cancelable=!1,this.notifyPlugins("afterEvent",a,i),(n||a.changed)&&this.render(),this}_handleEvent(t,e,a){const{_active:i=[],options:n}=this,r=e,h=this._getActiveElements(t,i,a,r),c=kb(t),l=xk(t,this._lastEvent,a,c);a&&(this._lastEvent=null,z(n.onHover,[t,h,this],this),c&&z(n.onClick,[t,h,this],this));const d=!p1(h,i);return(d||e)&&(this._active=h,this._updateHoverStyles(h,i,e)),this._lastEvent=l,d}_getActiveElements(t,e,a,i){if(t.type==="mouseout")return[];if(!a)return e;const n=this.options.hover;return this.getElementsAtEventForMode(t,n.mode,n,i)}}_(at,"defaults",W),_(at,"instances",l1),_(at,"overrides",Gt),_(at,"registry",vt),_(at,"version",gk),_(at,"getChart",d2);function p2(){return E(at.instances,s=>s._plugins.invalidate())}function mk(s,t,e){const{startAngle:a,x:i,y:n,outerRadius:r,innerRadius:h,options:c}=t,{borderWidth:l,borderJoinStyle:d}=c,p=Math.min(l/r,Q(a-e));if(s.beginPath(),s.arc(i,n,r-l/2,a+p/2,e-p/2),h>0){const g=Math.min(l/h,Q(a-e));s.arc(i,n,h+l/2,e-g/2,a+g/2,!0)}else{const g=Math.min(l/2,r*Q(a-e));if(d==="round")s.arc(i,n,g,e-O/2,a+O/2,!0);else if(d==="bevel"){const u=2*g*g,f=-u*Math.cos(e+O/2)+i,v=-u*Math.sin(e+O/2)+n,x=u*Math.cos(a+O/2)+i,m=u*Math.sin(a+O/2)+n;s.lineTo(f,v),s.lineTo(x,m)}}s.closePath(),s.moveTo(0,0),s.rect(0,0,s.canvas.width,s.canvas.height),s.clip("evenodd")}function Mk(s,t,e){const{startAngle:a,pixelMargin:i,x:n,y:r,outerRadius:h,innerRadius:c}=t;let l=i/h;s.beginPath(),s.arc(n,r,h,a-l,e+l),c>i?(l=i/c,s.arc(n,r,c,e+l,a-l,!0)):s.arc(n,r,i,e+U,a-U),s.closePath(),s.clip()}function yk(s){return us(s,["outerStart","outerEnd","innerStart","innerEnd"])}function bk(s,t,e,a){const i=yk(s.options.borderRadius),n=(e-t)/2,r=Math.min(n,a*t/2),h=c=>{const l=(e-Math.min(n,c))*a/2;return X(c,0,Math.min(n,l))};return{outerStart:h(i.outerStart),outerEnd:h(i.outerEnd),innerStart:X(i.innerStart,0,r),innerEnd:X(i.innerEnd,0,r)}}function te(s,t,e,a){return{x:e+s*Math.cos(t),y:a+s*Math.sin(t)}}function m1(s,t,e,a,i,n){const{x:r,y:h,startAngle:c,pixelMargin:l,innerRadius:d}=t,p=Math.max(t.outerRadius+a+e-l,0),g=d>0?d+a+e+l:0;let u=0;const f=i-c;if(a){const R=d>0?d-a:0,$=p>0?p-a:0,j=(R+$)/2,ht=j!==0?f*j/(j+a):f;u=(f-ht)/2}const v=Math.max(.001,f*p-e/O)/p,x=(f-v)/2,m=c+x+u,M=i-x-u,{outerStart:b,outerEnd:w,innerStart:y,innerEnd:k}=bk(t,g,p,M-m),C=p-b,S=p-w,L=m+b/C,P=M-w/S,D=g+y,B=g+k,Y=m+y/D,nt=M-k/B;if(s.beginPath(),n){const R=(L+P)/2;if(s.arc(r,h,p,L,R),s.arc(r,h,p,R,P),w>0){const K=te(S,P,r,h);s.arc(K.x,K.y,w,P,M+U)}const $=te(B,M,r,h);if(s.lineTo($.x,$.y),k>0){const K=te(B,nt,r,h);s.arc(K.x,K.y,k,M+U,nt+Math.PI)}const j=(M-k/g+(m+y/g))/2;if(s.arc(r,h,g,M-k/g,j,!0),s.arc(r,h,g,j,m+y/g,!0),y>0){const K=te(D,Y,r,h);s.arc(K.x,K.y,y,Y+Math.PI,m-U)}const ht=te(C,m,r,h);if(s.lineTo(ht.x,ht.y),b>0){const K=te(C,L,r,h);s.arc(K.x,K.y,b,m-U,L)}}else{s.moveTo(r,h);const R=Math.cos(L)*p+r,$=Math.sin(L)*p+h;s.lineTo(R,$);const j=Math.cos(P)*p+r,ht=Math.sin(P)*p+h;s.lineTo(j,ht)}s.closePath()}function wk(s,t,e,a,i){const{fullCircles:n,startAngle:r,circumference:h}=t;let c=t.endAngle;if(n){m1(s,t,e,a,c,i);for(let l=0;l<n;++l)s.fill();isNaN(h)||(c=r+(h%I||I))}return m1(s,t,e,a,c,i),s.fill(),c}function _k(s,t,e,a,i){const{fullCircles:n,startAngle:r,circumference:h,options:c}=t,{borderWidth:l,borderJoinStyle:d,borderDash:p,borderDashOffset:g,borderRadius:u}=c,f=c.borderAlign==="inner";if(!l)return;s.setLineDash(p||[]),s.lineDashOffset=g,f?(s.lineWidth=l*2,s.lineJoin=d||"round"):(s.lineWidth=l,s.lineJoin=d||"bevel");let v=t.endAngle;if(n){m1(s,t,e,a,v,i);for(let x=0;x<n;++x)s.stroke();isNaN(h)||(v=r+(h%I||I))}f&&Mk(s,t,v),c.selfJoin&&v-r>=O&&u===0&&d!=="miter"&&mk(s,t,v),n||(m1(s,t,e,a,v,i),s.stroke())}class ye extends dt{constructor(e){super();_(this,"circumference");_(this,"endAngle");_(this,"fullCircles");_(this,"innerRadius");_(this,"outerRadius");_(this,"pixelMargin");_(this,"startAngle");this.options=void 0,this.circumference=void 0,this.startAngle=void 0,this.endAngle=void 0,this.innerRadius=void 0,this.outerRadius=void 0,this.pixelMargin=0,this.fullCircles=0,e&&Object.assign(this,e)}inRange(e,a,i){const n=this.getProps(["x","y"],i),{angle:r,distance:h}=X2(n,{x:e,y:a}),{startAngle:c,endAngle:l,innerRadius:d,outerRadius:p,circumference:g}=this.getProps(["startAngle","endAngle","innerRadius","outerRadius","circumference"],i),u=(this.options.spacing+this.options.borderWidth)/2,f=H(g,l-c),v=Be(r,c,l)&&c!==l,x=f>=I||v,m=wt(h,d+u,p+u);return x&&m}getCenterPoint(e){const{x:a,y:i,startAngle:n,endAngle:r,innerRadius:h,outerRadius:c}=this.getProps(["x","y","startAngle","endAngle","innerRadius","outerRadius"],e),{offset:l,spacing:d}=this.options,p=(n+r)/2,g=(h+c+d+l)/2;return{x:a+Math.cos(p)*g,y:i+Math.sin(p)*g}}tooltipPosition(e){return this.getCenterPoint(e)}draw(e){const{options:a,circumference:i}=this,n=(a.offset||0)/4,r=(a.spacing||0)/2,h=a.circular;if(this.pixelMargin=a.borderAlign==="inner"?.33:0,this.fullCircles=i>I?Math.floor(i/I):0,i===0||this.innerRadius<0||this.outerRadius<0)return;e.save();const c=(this.startAngle+this.endAngle)/2;e.translate(Math.cos(c)*n,Math.sin(c)*n);const l=1-Math.sin(Math.min(O,i||0)),d=n*l;e.fillStyle=a.backgroundColor,e.strokeStyle=a.borderColor,wk(e,this,d,r,h),_k(e,this,d,r,h),e.restore()}}_(ye,"id","arc"),_(ye,"defaults",{borderAlign:"center",borderColor:"#fff",borderDash:[],borderDashOffset:0,borderJoinStyle:void 0,borderRadius:0,borderWidth:2,offset:0,spacing:0,angle:void 0,circular:!0,selfJoin:!1}),_(ye,"defaultRoutes",{backgroundColor:"backgroundColor"}),_(ye,"descriptors",{_scriptable:!0,_indexable:e=>e!=="borderDash"});function Hi(s,t,e=t){s.lineCap=H(e.borderCapStyle,t.borderCapStyle),s.setLineDash(H(e.borderDash,t.borderDash)),s.lineDashOffset=H(e.borderDashOffset,t.borderDashOffset),s.lineJoin=H(e.borderJoinStyle,t.borderJoinStyle),s.lineWidth=H(e.borderWidth,t.borderWidth),s.strokeStyle=H(e.borderColor,t.borderColor)}function kk(s,t,e){s.lineTo(e.x,e.y)}function Ck(s){return s.stepped?qb:s.tension||s.cubicInterpolationMode==="monotone"?Gb:kk}function Vi(s,t,e={}){const a=s.length,{start:i=0,end:n=a-1}=e,{start:r,end:h}=t,c=Math.max(i,r),l=Math.min(n,h),d=i<r&&n<r||i>h&&n>h;return{count:a,start:c,loop:t.loop,ilen:l<c&&!d?a+l-c:l-c}}function Sk(s,t,e,a){const{points:i,options:n}=t,{count:r,start:h,loop:c,ilen:l}=Vi(i,e,a),d=Ck(n);let{move:p=!0,reverse:g}=a||{},u,f,v;for(u=0;u<=l;++u)f=i[(h+(g?l-u:u))%r],!f.skip&&(p?(s.moveTo(f.x,f.y),p=!1):d(s,v,f,g,n.stepped),v=f);return c&&(f=i[(h+(g?l:0))%r],d(s,v,f,g,n.stepped)),!!c}function Lk(s,t,e,a){const i=t.points,{count:n,start:r,ilen:h}=Vi(i,e,a),{move:c=!0,reverse:l}=a||{};let d=0,p=0,g,u,f,v,x,m;const M=w=>(r+(l?h-w:w))%n,b=()=>{v!==x&&(s.lineTo(d,x),s.lineTo(d,v),s.lineTo(d,m))};for(c&&(u=i[M(0)],s.moveTo(u.x,u.y)),g=0;g<=h;++g){if(u=i[M(g)],u.skip)continue;const w=u.x,y=u.y,k=w|0;k===f?(y<v?v=y:y>x&&(x=y),d=(p*d+w)/++p):(b(),s.lineTo(w,y),f=k,p=0,v=x=y),m=y}b()}function Q1(s){const t=s.options,e=t.borderDash&&t.borderDash.length;return!s._decimated&&!s._loop&&!t.tension&&t.cubicInterpolationMode!=="monotone"&&!t.stepped&&!e?Lk:Sk}function Ak(s){return s.stepped?Sw:s.tension||s.cubicInterpolationMode==="monotone"?Lw:$t}function Hk(s,t,e,a){let i=t._path;i||(i=t._path=new Path2D,t.path(i,e,a)&&i.closePath()),Hi(s,t.options),s.stroke(i)}function Vk(s,t,e,a){const{segments:i,options:n}=t,r=Q1(t);for(const h of i)Hi(s,n,h.style),s.beginPath(),r(s,t,h,{start:e,end:e+a-1})&&s.closePath(),s.stroke()}const Pk=typeof Path2D=="function";function Dk(s,t,e,a){Pk&&!t.options.segment?Hk(s,t,e,a):Vk(s,t,e,a)}class Ct extends dt{constructor(t){super(),this.animated=!0,this.options=void 0,this._chart=void 0,this._loop=void 0,this._fullLoop=void 0,this._path=void 0,this._points=void 0,this._segments=void 0,this._decimated=!1,this._pointsUpdated=!1,this._datasetIndex=void 0,t&&Object.assign(this,t)}updateControlPoints(t,e){const a=this.options;if((a.tension||a.cubicInterpolationMode==="monotone")&&!a.stepped&&!this._pointsUpdated){const i=a.spanGaps?this._loop:this._fullLoop;mw(this._points,a,t,i,e),this._pointsUpdated=!0}}set points(t){this._points=t,delete this._segments,delete this._path,this._pointsUpdated=!1}get points(){return this._points}get segments(){return this._segments||(this._segments=Fw(this,this.options.segment))}first(){const t=this.segments,e=this.points;return t.length&&e[t[0].start]}last(){const t=this.segments,e=this.points,a=t.length;return a&&e[t[a-1].end]}interpolate(t,e){const a=this.options,i=t[e],n=this.points,r=fi(this,{property:e,start:i,end:i});if(!r.length)return;const h=[],c=Ak(a);let l,d;for(l=0,d=r.length;l<d;++l){const{start:p,end:g}=r[l],u=n[p],f=n[g];if(u===f){h.push(u);continue}const v=Math.abs((i-u[e])/(f[e]-u[e])),x=c(u,f,v,a.stepped);x[e]=t[e],h.push(x)}return h.length===1?h[0]:h}pathSegment(t,e,a){return Q1(this)(t,this,e,a)}path(t,e,a){const i=this.segments,n=Q1(this);let r=this._loop;e=e||0,a=a||this.points.length-e;for(const h of i)r&=n(t,this,h,{start:e,end:e+a-1});return!!r}draw(t,e,a,i){const n=this.options||{};(this.points||[]).length&&n.borderWidth&&(t.save(),Dk(t,this,a,i),t.restore()),this.animated&&(this._pointsUpdated=!1,this._path=void 0)}}_(Ct,"id","line"),_(Ct,"defaults",{borderCapStyle:"butt",borderDash:[],borderDashOffset:0,borderJoinStyle:"miter",borderWidth:3,capBezierPoints:!0,cubicInterpolationMode:"default",fill:!1,spanGaps:!1,stepped:!1,tension:0}),_(Ct,"defaultRoutes",{backgroundColor:"backgroundColor",borderColor:"borderColor"}),_(Ct,"descriptors",{_scriptable:!0,_indexable:t=>t!=="borderDash"&&t!=="fill"});function g2(s,t,e,a){const i=s.options,{[e]:n}=s.getProps([e],a);return Math.abs(t-n)<i.radius+i.hitRadius}class Ve extends dt{constructor(e){super();_(this,"parsed");_(this,"skip");_(this,"stop");this.options=void 0,this.parsed=void 0,this.skip=void 0,this.stop=void 0,e&&Object.assign(this,e)}inRange(e,a,i){const n=this.options,{x:r,y:h}=this.getProps(["x","y"],i);return Math.pow(e-r,2)+Math.pow(a-h,2)<Math.pow(n.hitRadius+n.radius,2)}inXRange(e,a){return g2(this,e,"x",a)}inYRange(e,a){return g2(this,e,"y",a)}getCenterPoint(e){const{x:a,y:i}=this.getProps(["x","y"],e);return{x:a,y:i}}size(e){e=e||this.options||{};let a=e.radius||0;a=Math.max(a,a&&e.hoverRadius||0);const i=a&&e.borderWidth||0;return(a+i)*2}draw(e,a){const i=this.options;this.skip||i.radius<.1||!kt(this,a,this.size(i)/2)||(e.strokeStyle=i.borderColor,e.lineWidth=i.borderWidth,e.fillStyle=i.backgroundColor,X1(e,i,this.x,this.y))}getRange(){const e=this.options||{};return e.radius+e.hitRadius}}_(Ve,"id","point"),_(Ve,"defaults",{borderWidth:1,hitRadius:1,hoverBorderWidth:1,hoverRadius:4,pointStyle:"circle",radius:3,rotation:0}),_(Ve,"defaultRoutes",{backgroundColor:"backgroundColor",borderColor:"borderColor"});function Pi(s,t){const{x:e,y:a,base:i,width:n,height:r}=s.getProps(["x","y","base","width","height"],t);let h,c,l,d,p;return s.horizontal?(p=r/2,h=Math.min(e,i),c=Math.max(e,i),l=a-p,d=a+p):(p=n/2,h=e-p,c=e+p,l=Math.min(a,i),d=Math.max(a,i)),{left:h,top:l,right:c,bottom:d}}function Ht(s,t,e,a){return s?0:X(t,e,a)}function Fk(s,t,e){const a=s.options.borderWidth,i=s.borderSkipped,n=ii(a);return{t:Ht(i.top,n.top,0,e),r:Ht(i.right,n.right,0,t),b:Ht(i.bottom,n.bottom,0,e),l:Ht(i.left,n.left,0,t)}}function Tk(s,t,e){const{enableBorderRadius:a}=s.getProps(["enableBorderRadius"]),i=s.options.borderRadius,n=jt(i),r=Math.min(t,e),h=s.borderSkipped,c=a||T(i);return{topLeft:Ht(!c||h.top||h.left,n.topLeft,0,r),topRight:Ht(!c||h.top||h.right,n.topRight,0,r),bottomLeft:Ht(!c||h.bottom||h.left,n.bottomLeft,0,r),bottomRight:Ht(!c||h.bottom||h.right,n.bottomRight,0,r)}}function Bk(s){const t=Pi(s),e=t.right-t.left,a=t.bottom-t.top,i=Fk(s,e/2,a/2),n=Tk(s,e/2,a/2);return{outer:{x:t.left,y:t.top,w:e,h:a,radius:n},inner:{x:t.left+i.l,y:t.top+i.t,w:e-i.l-i.r,h:a-i.t-i.b,radius:{topLeft:Math.max(0,n.topLeft-Math.max(i.t,i.l)),topRight:Math.max(0,n.topRight-Math.max(i.t,i.r)),bottomLeft:Math.max(0,n.bottomLeft-Math.max(i.b,i.l)),bottomRight:Math.max(0,n.bottomRight-Math.max(i.b,i.r))}}}}function $1(s,t,e,a){const i=t===null,n=e===null,h=s&&!(i&&n)&&Pi(s,a);return h&&(i||wt(t,h.left,h.right))&&(n||wt(e,h.top,h.bottom))}function Ok(s){return s.topLeft||s.topRight||s.bottomLeft||s.bottomRight}function Ek(s,t){s.rect(t.x,t.y,t.w,t.h)}function Z1(s,t,e={}){const a=s.x!==e.x?-t:0,i=s.y!==e.y?-t:0,n=(s.x+s.w!==e.x+e.w?t:0)-a,r=(s.y+s.h!==e.y+e.h?t:0)-i;return{x:s.x+a,y:s.y+i,w:s.w+n,h:s.h+r,radius:s.radius}}class d1 extends dt{constructor(t){super(),this.options=void 0,this.horizontal=void 0,this.base=void 0,this.width=void 0,this.height=void 0,this.inflateAmount=void 0,t&&Object.assign(this,t)}draw(t){const{inflateAmount:e,options:{borderColor:a,backgroundColor:i}}=this,{inner:n,outer:r}=Bk(this),h=Ok(r.radius)?Oe:Ek;t.save(),(r.w!==n.w||r.h!==n.h)&&(t.beginPath(),h(t,Z1(r,e,n)),t.clip(),h(t,Z1(n,-e,r)),t.fillStyle=a,t.fill("evenodd")),t.beginPath(),h(t,Z1(n,e)),t.fillStyle=i,t.fill(),t.restore()}inRange(t,e,a){return $1(this,t,e,a)}inXRange(t,e){return $1(this,t,null,e)}inYRange(t,e){return $1(this,null,t,e)}getCenterPoint(t){const{x:e,y:a,base:i,horizontal:n}=this.getProps(["x","y","base","horizontal"],t);return{x:n?(e+i)/2:e,y:n?a:(a+i)/2}}getRange(t){return t==="x"?this.width/2:this.height/2}}_(d1,"id","bar"),_(d1,"defaults",{borderSkipped:"start",borderWidth:0,borderRadius:0,inflateAmount:"auto",pointStyle:void 0}),_(d1,"defaultRoutes",{backgroundColor:"backgroundColor",borderColor:"borderColor"});var Rk=Object.freeze({__proto__:null,ArcElement:ye,BarElement:d1,LineElement:Ct,PointElement:Ve});const ts=["rgb(54, 162, 235)","rgb(255, 99, 132)","rgb(255, 159, 64)","rgb(255, 205, 86)","rgb(75, 192, 192)","rgb(153, 102, 255)","rgb(201, 203, 207)"],u2=ts.map(s=>s.replace("rgb(","rgba(").replace(")",", 0.5)"));function Di(s){return ts[s%ts.length]}function Fi(s){return u2[s%u2.length]}function zk(s,t){return s.borderColor=Di(t),s.backgroundColor=Fi(t),++t}function Ik(s,t){return s.backgroundColor=s.data.map(()=>Di(t++)),t}function $k(s,t){return s.backgroundColor=s.data.map(()=>Fi(t++)),t}function Zk(s){let t=0;return(e,a)=>{const i=s.getDatasetMeta(a).controller;i instanceof Nt?t=Ik(e,t):i instanceof He?t=$k(e,t):i&&(t=zk(e,t))}}function f2(s){let t;for(t in s)if(s[t].borderColor||s[t].backgroundColor)return!0;return!1}function Wk(s){return s&&(s.borderColor||s.backgroundColor)}function Nk(){return W.borderColor!=="rgba(0,0,0,0.1)"||W.backgroundColor!=="rgba(0,0,0,0.1)"}var jk={id:"colors",defaults:{enabled:!0,forceOverride:!1},beforeLayout(s,t,e){if(!e.enabled)return;const{data:{datasets:a},options:i}=s.config,{elements:n}=i,r=f2(a)||Wk(i)||n&&f2(n)||Nk();if(!e.forceOverride&&r)return;const h=Zk(s);a.forEach(h)}};function Uk(s,t,e,a,i){const n=i.samples||a;if(n>=e)return s.slice(t,t+e);const r=[],h=(e-2)/(n-2);let c=0;const l=t+e-1;let d=t,p,g,u,f,v;for(r[c++]=s[d],p=0;p<n-2;p++){let x=0,m=0,M;const b=Math.floor((p+1)*h)+1+t,w=Math.min(Math.floor((p+2)*h)+1,e)+t,y=w-b;for(M=b;M<w;M++)x+=s[M].x,m+=s[M].y;x/=y,m/=y;const k=Math.floor(p*h)+1+t,C=Math.min(Math.floor((p+1)*h)+1,e)+t,{x:S,y:L}=s[d];for(u=f=-1,M=k;M<C;M++)f=.5*Math.abs((S-x)*(s[M].y-L)-(S-s[M].x)*(m-L)),f>u&&(u=f,g=s[M],v=M);r[c++]=g,d=v}return r[c++]=s[l],r}function qk(s,t,e,a){let i=0,n=0,r,h,c,l,d,p,g,u,f,v;const x=[],m=t+e-1,M=s[t].x,w=s[m].x-M;for(r=t;r<t+e;++r){h=s[r],c=(h.x-M)/w*a,l=h.y;const y=c|0;if(y===d)l<f?(f=l,p=r):l>v&&(v=l,g=r),i=(n*i+h.x)/++n;else{const k=r-1;if(!F(p)&&!F(g)){const C=Math.min(p,g),S=Math.max(p,g);C!==u&&C!==k&&x.push({...s[C],x:i}),S!==u&&S!==k&&x.push({...s[S],x:i})}r>0&&k!==u&&x.push(s[k]),x.push(h),d=y,n=0,f=v=l,p=g=u=r}}return x}function Ti(s){if(s._decimated){const t=s._data;delete s._decimated,delete s._data,Object.defineProperty(s,"data",{configurable:!0,enumerable:!0,writable:!0,value:t})}}function v2(s){s.data.datasets.forEach(t=>{Ti(t)})}function Gk(s,t){const e=t.length;let a=0,i;const{iScale:n}=s,{min:r,max:h,minDefined:c,maxDefined:l}=n.getUserBounds();return c&&(a=X(_t(t,n.axis,r).lo,0,e-1)),l?i=X(_t(t,n.axis,h).hi+1,a,e)-a:i=e-a,{start:a,count:i}}var Xk={id:"decimation",defaults:{algorithm:"min-max",enabled:!1},beforeElementsUpdate:(s,t,e)=>{if(!e.enabled){v2(s);return}const a=s.width;s.data.datasets.forEach((i,n)=>{const{_data:r,indexAxis:h}=i,c=s.getDatasetMeta(n),l=r||i.data;if(me([h,s.options.indexAxis])==="y"||!c.controller.supportsDecimation)return;const d=s.scales[c.xAxisID];if(d.type!=="linear"&&d.type!=="time"||s.options.parsing)return;let{start:p,count:g}=Gk(c,l);const u=e.threshold||4*a;if(g<=u){Ti(i);return}F(r)&&(i._data=l,delete i.data,Object.defineProperty(i,"data",{configurable:!0,enumerable:!0,get:function(){return this._decimated},set:function(v){this._data=v}}));let f;switch(e.algorithm){case"lttb":f=Uk(l,p,g,a,e);break;case"min-max":f=qk(l,p,g,a);break;default:throw new Error(`Unsupported decimation algorithm '${e.algorithm}'`)}i._decimated=f})},destroy(s){v2(s)}};function Yk(s,t,e){const a=s.segments,i=s.points,n=t.points,r=[];for(const h of a){let{start:c,end:l}=h;l=L1(c,l,i);const d=es(e,i[c],i[l],h.loop);if(!t.segments){r.push({source:h,target:d,start:i[c],end:i[l]});continue}const p=fi(t,d);for(const g of p){const u=es(e,n[g.start],n[g.end],g.loop),f=ui(h,i,u);for(const v of f)r.push({source:v,target:g,start:{[e]:x2(d,u,"start",Math.max)},end:{[e]:x2(d,u,"end",Math.min)}})}}return r}function es(s,t,e,a){if(a)return;let i=t[s],n=e[s];return s==="angle"&&(i=Q(i),n=Q(n)),{property:s,start:i,end:n}}function Kk(s,t){const{x:e=null,y:a=null}=s||{},i=t.points,n=[];return t.segments.forEach(({start:r,end:h})=>{h=L1(r,h,i);const c=i[r],l=i[h];a!==null?(n.push({x:c.x,y:a}),n.push({x:l.x,y:a})):e!==null&&(n.push({x:e,y:c.y}),n.push({x:e,y:l.y}))}),n}function L1(s,t,e){for(;t>s;t--){const a=e[t];if(!isNaN(a.x)&&!isNaN(a.y))break}return t}function x2(s,t,e,a){return s&&t?a(s[e],t[e]):s?s[e]:t?t[e]:0}function Bi(s,t){let e=[],a=!1;return Z(s)?(a=!0,e=s):e=Kk(s,t),e.length?new Ct({points:e,options:{tension:0},_loop:a,_fullLoop:a}):null}function m2(s){return s&&s.fill!==!1}function Jk(s,t,e){let i=s[t].fill;const n=[t];let r;if(!e)return i;for(;i!==!1&&n.indexOf(i)===-1;){if(!N(i))return i;if(r=s[i],!r)return!1;if(r.visible)return i;n.push(i),i=r.fill}return!1}function Qk(s,t,e){const a=aC(s);if(T(a))return isNaN(a.value)?!1:a;let i=parseFloat(a);return N(i)&&Math.floor(i)===i?tC(a[0],t,i,e):["origin","start","end","stack","shape"].indexOf(a)>=0&&a}function tC(s,t,e,a){return(s==="-"||s==="+")&&(e=t+e),e===t||e<0||e>=a?!1:e}function eC(s,t){let e=null;return s==="start"?e=t.bottom:s==="end"?e=t.top:T(s)?e=t.getPixelForValue(s.value):t.getBasePixel&&(e=t.getBasePixel()),e}function sC(s,t,e){let a;return s==="start"?a=e:s==="end"?a=t.options.reverse?t.min:t.max:T(s)?a=s.value:a=t.getBaseValue(),a}function aC(s){const t=s.options,e=t.fill;let a=H(e&&e.target,e);return a===void 0&&(a=!!t.backgroundColor),a===!1||a===null?!1:a===!0?"origin":a}function iC(s){const{scale:t,index:e,line:a}=s,i=[],n=a.segments,r=a.points,h=nC(t,e);h.push(Bi({x:null,y:t.bottom},a));for(let c=0;c<n.length;c++){const l=n[c];for(let d=l.start;d<=l.end;d++)oC(i,r[d],h)}return new Ct({points:i,options:{}})}function nC(s,t){const e=[],a=s.getMatchingVisibleMetas("line");for(let i=0;i<a.length;i++){const n=a[i];if(n.index===t)break;n.hidden||e.unshift(n.dataset)}return e}function oC(s,t,e){const a=[];for(let i=0;i<e.length;i++){const n=e[i],{first:r,last:h,point:c}=rC(n,t,"x");if(!(!c||r&&h)){if(r)a.unshift(c);else if(s.push(c),!h)break}}s.push(...a)}function rC(s,t,e){const a=s.interpolate(t,e);if(!a)return{};const i=a[e],n=s.segments,r=s.points;let h=!1,c=!1;for(let l=0;l<n.length;l++){const d=n[l],p=r[d.start][e],g=r[d.end][e];if(wt(i,p,g)){h=i===p,c=i===g;break}}return{first:h,last:c,point:a}}class Oi{constructor(t){this.x=t.x,this.y=t.y,this.radius=t.radius}pathSegment(t,e,a){const{x:i,y:n,radius:r}=this;return e=e||{start:0,end:I},t.arc(i,n,r,e.end,e.start,!0),!a.bounds}interpolate(t){const{x:e,y:a,radius:i}=this,n=t.angle;return{x:e+Math.cos(n)*i,y:a+Math.sin(n)*i,angle:n}}}function hC(s){const{chart:t,fill:e,line:a}=s;if(N(e))return cC(t,e);if(e==="stack")return iC(s);if(e==="shape")return!0;const i=lC(s);return i instanceof Oi?i:Bi(i,a)}function cC(s,t){const e=s.getDatasetMeta(t);return e&&s.isDatasetVisible(t)?e.dataset:null}function lC(s){return(s.scale||{}).getPointPositionForValue?pC(s):dC(s)}function dC(s){const{scale:t={},fill:e}=s,a=eC(e,t);if(N(a)){const i=t.isHorizontal();return{x:i?a:null,y:i?null:a}}return null}function pC(s){const{scale:t,fill:e}=s,a=t.options,i=t.getLabels().length,n=a.reverse?t.max:t.min,r=sC(e,t,n),h=[];if(a.grid.circular){const c=t.getPointPositionForValue(0,n);return new Oi({x:c.x,y:c.y,radius:t.getDistanceFromCenterForValue(r)})}for(let c=0;c<i;++c)h.push(t.getPointPositionForValue(c,r));return h}function W1(s,t,e){const a=hC(t),{chart:i,index:n,line:r,scale:h,axis:c}=t,l=r.options,d=l.fill,p=l.backgroundColor,{above:g=p,below:u=p}=d||{},f=i.getDatasetMeta(n),v=vi(i,f);a&&r.points.length&&(_1(s,e),gC(s,{line:r,target:a,above:g,below:u,area:e,scale:h,axis:c,clip:v}),k1(s))}function gC(s,t){const{line:e,target:a,above:i,below:n,area:r,scale:h,clip:c}=t,l=e._loop?"angle":t.axis;s.save();let d=n;n!==i&&(l==="x"?(M2(s,a,r.top),N1(s,{line:e,target:a,color:i,scale:h,property:l,clip:c}),s.restore(),s.save(),M2(s,a,r.bottom)):l==="y"&&(y2(s,a,r.left),N1(s,{line:e,target:a,color:n,scale:h,property:l,clip:c}),s.restore(),s.save(),y2(s,a,r.right),d=i)),N1(s,{line:e,target:a,color:d,scale:h,property:l,clip:c}),s.restore()}function M2(s,t,e){const{segments:a,points:i}=t;let n=!0,r=!1;s.beginPath();for(const h of a){const{start:c,end:l}=h,d=i[c],p=i[L1(c,l,i)];n?(s.moveTo(d.x,d.y),n=!1):(s.lineTo(d.x,e),s.lineTo(d.x,d.y)),r=!!t.pathSegment(s,h,{move:r}),r?s.closePath():s.lineTo(p.x,e)}s.lineTo(t.first().x,e),s.closePath(),s.clip()}function y2(s,t,e){const{segments:a,points:i}=t;let n=!0,r=!1;s.beginPath();for(const h of a){const{start:c,end:l}=h,d=i[c],p=i[L1(c,l,i)];n?(s.moveTo(d.x,d.y),n=!1):(s.lineTo(e,d.y),s.lineTo(d.x,d.y)),r=!!t.pathSegment(s,h,{move:r}),r?s.closePath():s.lineTo(e,p.y)}s.lineTo(e,t.first().y),s.closePath(),s.clip()}function N1(s,t){const{line:e,target:a,property:i,color:n,scale:r,clip:h}=t,c=Yk(e,a,i);for(const{source:l,target:d,start:p,end:g}of c){const{style:{backgroundColor:u=n}={}}=l,f=a!==!0;s.save(),s.fillStyle=u,uC(s,r,h,f&&es(i,p,g)),s.beginPath();const v=!!e.pathSegment(s,l);let x;if(f){v?s.closePath():b2(s,a,g,i);const m=!!a.pathSegment(s,d,{move:v,reverse:!0});x=v&&m,x||b2(s,a,p,i)}s.closePath(),s.fill(x?"evenodd":"nonzero"),s.restore()}}function uC(s,t,e,a){const i=t.chart.chartArea,{property:n,start:r,end:h}=a||{};if(n==="x"||n==="y"){let c,l,d,p;n==="x"?(c=r,l=i.top,d=h,p=i.bottom):(c=i.left,l=r,d=i.right,p=h),s.beginPath(),e&&(c=Math.max(c,e.left),d=Math.min(d,e.right),l=Math.max(l,e.top),p=Math.min(p,e.bottom)),s.rect(c,l,d-c,p-l),s.clip()}}function b2(s,t,e,a){const i=t.interpolate(e,a);i&&s.lineTo(i.x,i.y)}var Ei={id:"filler",afterDatasetsUpdate(s,t,e){const a=(s.data.datasets||[]).length,i=[];let n,r,h,c;for(r=0;r<a;++r)n=s.getDatasetMeta(r),h=n.dataset,c=null,h&&h.options&&h instanceof Ct&&(c={visible:s.isDatasetVisible(r),index:r,fill:Qk(h,r,a),chart:s,axis:n.controller.options.indexAxis,scale:n.vScale,line:h}),n.$filler=c,i.push(c);for(r=0;r<a;++r)c=i[r],!(!c||c.fill===!1)&&(c.fill=Jk(i,r,e.propagate))},beforeDraw(s,t,e){const a=e.drawTime==="beforeDraw",i=s.getSortedVisibleDatasetMetas(),n=s.chartArea;for(let r=i.length-1;r>=0;--r){const h=i[r].$filler;h&&(h.line.updateControlPoints(n,h.axis),a&&h.fill&&W1(s.ctx,h,n))}},beforeDatasetsDraw(s,t,e){if(e.drawTime!=="beforeDatasetsDraw")return;const a=s.getSortedVisibleDatasetMetas();for(let i=a.length-1;i>=0;--i){const n=a[i].$filler;m2(n)&&W1(s.ctx,n,s.chartArea)}},beforeDatasetDraw(s,t,e){const a=t.meta.$filler;!m2(a)||e.drawTime!=="beforeDatasetDraw"||W1(s.ctx,a,s.chartArea)},defaults:{propagate:!0,drawTime:"beforeDatasetDraw"}};const w2=(s,t)=>{let{boxHeight:e=t,boxWidth:a=t}=s;return s.usePointStyle&&(e=Math.min(e,t),a=s.pointStyleWidth||Math.min(a,t)),{boxWidth:a,boxHeight:e,itemHeight:Math.max(t,e)}},fC=(s,t)=>s!==null&&t!==null&&s.datasetIndex===t.datasetIndex&&s.index===t.index;class _2 extends dt{constructor(t){super(),this._added=!1,this.legendHitBoxes=[],this._hoveredItem=null,this.doughnutMode=!1,this.chart=t.chart,this.options=t.options,this.ctx=t.ctx,this.legendItems=void 0,this.columnSizes=void 0,this.lineWidths=void 0,this.maxHeight=void 0,this.maxWidth=void 0,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.height=void 0,this.width=void 0,this._margins=void 0,this.position=void 0,this.weight=void 0,this.fullSize=void 0}update(t,e,a){this.maxWidth=t,this.maxHeight=e,this._margins=a,this.setDimensions(),this.buildLabels(),this.fit()}setDimensions(){this.isHorizontal()?(this.width=this.maxWidth,this.left=this._margins.left,this.right=this.width):(this.height=this.maxHeight,this.top=this._margins.top,this.bottom=this.height)}buildLabels(){const t=this.options.labels||{};let e=z(t.generateLabels,[this.chart],this)||[];t.filter&&(e=e.filter(a=>t.filter(a,this.chart.data))),t.sort&&(e=e.sort((a,i)=>t.sort(a,i,this.chart.data))),this.options.reverse&&e.reverse(),this.legendItems=e}fit(){const{options:t,ctx:e}=this;if(!t.display){this.width=this.height=0;return}const a=t.labels,i=G(a.font),n=i.size,r=this._computeTitleHeight(),{boxWidth:h,itemHeight:c}=w2(a,n);let l,d;e.font=i.string,this.isHorizontal()?(l=this.maxWidth,d=this._fitRows(r,n,h,c)+10):(d=this.maxHeight,l=this._fitCols(r,i,h,c)+10),this.width=Math.min(l,t.maxWidth||this.maxWidth),this.height=Math.min(d,t.maxHeight||this.maxHeight)}_fitRows(t,e,a,i){const{ctx:n,maxWidth:r,options:{labels:{padding:h}}}=this,c=this.legendHitBoxes=[],l=this.lineWidths=[0],d=i+h;let p=t;n.textAlign="left",n.textBaseline="middle";let g=-1,u=-d;return this.legendItems.forEach((f,v)=>{const x=a+e/2+n.measureText(f.text).width;(v===0||l[l.length-1]+x+2*h>r)&&(p+=d,l[l.length-(v>0?0:1)]=0,u+=d,g++),c[v]={left:0,top:u,row:g,width:x,height:i},l[l.length-1]+=x+h}),p}_fitCols(t,e,a,i){const{ctx:n,maxHeight:r,options:{labels:{padding:h}}}=this,c=this.legendHitBoxes=[],l=this.columnSizes=[],d=r-t;let p=h,g=0,u=0,f=0,v=0;return this.legendItems.forEach((x,m)=>{const{itemWidth:M,itemHeight:b}=vC(a,e,n,x,i);m>0&&u+b+2*h>d&&(p+=g+h,l.push({width:g,height:u}),f+=g+h,v++,g=u=0),c[m]={left:f,top:u,col:v,width:M,height:b},g=Math.max(g,M),u+=b+h}),p+=g,l.push({width:g,height:u}),p}adjustHitBoxes(){if(!this.options.display)return;const t=this._computeTitleHeight(),{legendHitBoxes:e,options:{align:a,labels:{padding:i},rtl:n}}=this,r=se(n,this.left,this.width);if(this.isHorizontal()){let h=0,c=J(a,this.left+i,this.right-this.lineWidths[h]);for(const l of e)h!==l.row&&(h=l.row,c=J(a,this.left+i,this.right-this.lineWidths[h])),l.top+=this.top+t+i,l.left=r.leftForLtr(r.x(c),l.width),c+=l.width+i}else{let h=0,c=J(a,this.top+t+i,this.bottom-this.columnSizes[h].height);for(const l of e)l.col!==h&&(h=l.col,c=J(a,this.top+t+i,this.bottom-this.columnSizes[h].height)),l.top=c,l.left+=this.left+i,l.left=r.leftForLtr(r.x(l.left),l.width),c+=l.height+i}}isHorizontal(){return this.options.position==="top"||this.options.position==="bottom"}draw(){if(this.options.display){const t=this.ctx;_1(t,this),this._draw(),k1(t)}}_draw(){const{options:t,columnSizes:e,lineWidths:a,ctx:i}=this,{align:n,labels:r}=t,h=W.color,c=se(t.rtl,this.left,this.width),l=G(r.font),{padding:d}=r,p=l.size,g=p/2;let u;this.drawTitle(),i.textAlign=c.textAlign("left"),i.textBaseline="middle",i.lineWidth=.5,i.font=l.string;const{boxWidth:f,boxHeight:v,itemHeight:x}=w2(r,p),m=function(k,C,S){if(isNaN(f)||f<=0||isNaN(v)||v<0)return;i.save();const L=H(S.lineWidth,1);if(i.fillStyle=H(S.fillStyle,h),i.lineCap=H(S.lineCap,"butt"),i.lineDashOffset=H(S.lineDashOffset,0),i.lineJoin=H(S.lineJoin,"miter"),i.lineWidth=L,i.strokeStyle=H(S.strokeStyle,h),i.setLineDash(H(S.lineDash,[])),r.usePointStyle){const P={radius:v*Math.SQRT2/2,pointStyle:S.pointStyle,rotation:S.rotation,borderWidth:L},D=c.xPlus(k,f/2),B=C+g;ai(i,P,D,B,r.pointStyleWidth&&f)}else{const P=C+Math.max((p-v)/2,0),D=c.leftForLtr(k,f),B=jt(S.borderRadius);i.beginPath(),Object.values(B).some(Y=>Y!==0)?Oe(i,{x:D,y:P,w:f,h:v,radius:B}):i.rect(D,P,f,v),i.fill(),L!==0&&i.stroke()}i.restore()},M=function(k,C,S){Xt(i,S.text,k,C+x/2,l,{strikethrough:S.hidden,textAlign:c.textAlign(S.textAlign)})},b=this.isHorizontal(),w=this._computeTitleHeight();b?u={x:J(n,this.left+d,this.right-a[0]),y:this.top+d+w,line:0}:u={x:this.left+d,y:J(n,this.top+w+d,this.bottom-e[0].height),line:0},di(this.ctx,t.textDirection);const y=x+d;this.legendItems.forEach((k,C)=>{i.strokeStyle=k.fontColor,i.fillStyle=k.fontColor;const S=i.measureText(k.text).width,L=c.textAlign(k.textAlign||(k.textAlign=r.textAlign)),P=f+g+S;let D=u.x,B=u.y;c.setWidth(this.width),b?C>0&&D+P+d>this.right&&(B=u.y+=y,u.line++,D=u.x=J(n,this.left+d,this.right-a[u.line])):C>0&&B+y>this.bottom&&(D=u.x=D+e[u.line].width+d,u.line++,B=u.y=J(n,this.top+w+d,this.bottom-e[u.line].height));const Y=c.x(D);if(m(Y,B,k),D=Ob(L,D+f+g,b?D+P:this.right,t.rtl),M(c.x(D),B,k),b)u.x+=P+d;else if(typeof k.text!="string"){const nt=l.lineHeight;u.y+=Ri(k,nt)+d}else u.y+=y}),pi(this.ctx,t.textDirection)}drawTitle(){const t=this.options,e=t.title,a=G(e.font),i=et(e.padding);if(!e.display)return;const n=se(t.rtl,this.left,this.width),r=this.ctx,h=e.position,c=a.size/2,l=i.top+c;let d,p=this.left,g=this.width;if(this.isHorizontal())g=Math.max(...this.lineWidths),d=this.top+l,p=J(t.align,p,this.right-g);else{const f=this.columnSizes.reduce((v,x)=>Math.max(v,x.height),0);d=l+J(t.align,this.top,this.bottom-f-t.labels.padding-this._computeTitleHeight())}const u=J(h,p,p+g);r.textAlign=n.textAlign(ps(h)),r.textBaseline="middle",r.strokeStyle=e.color,r.fillStyle=e.color,r.font=a.string,Xt(r,e.text,u,d,a)}_computeTitleHeight(){const t=this.options.title,e=G(t.font),a=et(t.padding);return t.display?e.lineHeight+a.height:0}_getLegendItemAt(t,e){let a,i,n;if(wt(t,this.left,this.right)&&wt(e,this.top,this.bottom)){for(n=this.legendHitBoxes,a=0;a<n.length;++a)if(i=n[a],wt(t,i.left,i.left+i.width)&&wt(e,i.top,i.top+i.height))return this.legendItems[a]}return null}handleEvent(t){const e=this.options;if(!MC(t.type,e))return;const a=this._getLegendItemAt(t.x,t.y);if(t.type==="mousemove"||t.type==="mouseout"){const i=this._hoveredItem,n=fC(i,a);i&&!n&&z(e.onLeave,[t,i,this],this),this._hoveredItem=a,a&&!n&&z(e.onHover,[t,a,this],this)}else a&&z(e.onClick,[t,a,this],this)}}function vC(s,t,e,a,i){const n=xC(a,s,t,e),r=mC(i,a,t.lineHeight);return{itemWidth:n,itemHeight:r}}function xC(s,t,e,a){let i=s.text;return i&&typeof i!="string"&&(i=i.reduce((n,r)=>n.length>r.length?n:r)),t+e.size/2+a.measureText(i).width}function mC(s,t,e){let a=s;return typeof t.text!="string"&&(a=Ri(t,e)),a}function Ri(s,t){const e=s.text?s.text.length:0;return t*e}function MC(s,t){return!!((s==="mousemove"||s==="mouseout")&&(t.onHover||t.onLeave)||t.onClick&&(s==="click"||s==="mouseup"))}var zi={id:"legend",_element:_2,start(s,t,e){const a=s.legend=new _2({ctx:s.ctx,options:e,chart:s});tt.configure(s,a,e),tt.addBox(s,a)},stop(s){tt.removeBox(s,s.legend),delete s.legend},beforeUpdate(s,t,e){const a=s.legend;tt.configure(s,a,e),a.options=e},afterUpdate(s){const t=s.legend;t.buildLabels(),t.adjustHitBoxes()},afterEvent(s,t){t.replay||s.legend.handleEvent(t.event)},defaults:{display:!0,position:"top",align:"center",fullSize:!0,reverse:!1,weight:1e3,onClick(s,t,e){const a=t.datasetIndex,i=e.chart;i.isDatasetVisible(a)?(i.hide(a),t.hidden=!0):(i.show(a),t.hidden=!1)},onHover:null,onLeave:null,labels:{color:s=>s.chart.options.color,boxWidth:40,padding:10,generateLabels(s){const t=s.data.datasets,{labels:{usePointStyle:e,pointStyle:a,textAlign:i,color:n,useBorderRadius:r,borderRadius:h}}=s.legend.options;return s._getSortedDatasetMetas().map(c=>{const l=c.controller.getStyle(e?0:void 0),d=et(l.borderWidth);return{text:t[c.index].label,fillStyle:l.backgroundColor,fontColor:n,hidden:!c.visible,lineCap:l.borderCapStyle,lineDash:l.borderDash,lineDashOffset:l.borderDashOffset,lineJoin:l.borderJoinStyle,lineWidth:(d.width+d.height)/4,strokeStyle:l.borderColor,pointStyle:a||l.pointStyle,rotation:l.rotation,textAlign:i||l.textAlign,borderRadius:r&&(h||l.borderRadius),datasetIndex:c.index}},this)}},title:{color:s=>s.chart.options.color,display:!1,position:"center",text:""}},descriptors:{_scriptable:s=>!s.startsWith("on"),labels:{_scriptable:s=>!["generateLabels","filter","sort"].includes(s)}}};class bs extends dt{constructor(t){super(),this.chart=t.chart,this.options=t.options,this.ctx=t.ctx,this._padding=void 0,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.width=void 0,this.height=void 0,this.position=void 0,this.weight=void 0,this.fullSize=void 0}update(t,e){const a=this.options;if(this.left=0,this.top=0,!a.display){this.width=this.height=this.right=this.bottom=0;return}this.width=this.right=t,this.height=this.bottom=e;const i=Z(a.text)?a.text.length:1;this._padding=et(a.padding);const n=i*G(a.font).lineHeight+this._padding.height;this.isHorizontal()?this.height=n:this.width=n}isHorizontal(){const t=this.options.position;return t==="top"||t==="bottom"}_drawArgs(t){const{top:e,left:a,bottom:i,right:n,options:r}=this,h=r.align;let c=0,l,d,p;return this.isHorizontal()?(d=J(h,a,n),p=e+t,l=n-a):(r.position==="left"?(d=a+t,p=J(h,i,e),c=O*-.5):(d=n-t,p=J(h,e,i),c=O*.5),l=i-e),{titleX:d,titleY:p,maxWidth:l,rotation:c}}draw(){const t=this.ctx,e=this.options;if(!e.display)return;const a=G(e.font),n=a.lineHeight/2+this._padding.top,{titleX:r,titleY:h,maxWidth:c,rotation:l}=this._drawArgs(n);Xt(t,e.text,0,0,a,{color:e.color,maxWidth:c,rotation:l,textAlign:ps(e.align),textBaseline:"middle",translation:[r,h]})}}function yC(s,t){const e=new bs({ctx:s.ctx,options:t,chart:s});tt.configure(s,e,t),tt.addBox(s,e),s.titleBlock=e}var Ii={id:"title",_element:bs,start(s,t,e){yC(s,e)},stop(s){const t=s.titleBlock;tt.removeBox(s,t),delete s.titleBlock},beforeUpdate(s,t,e){const a=s.titleBlock;tt.configure(s,a,e),a.options=e},defaults:{align:"center",display:!1,font:{weight:"bold"},fullSize:!0,padding:10,position:"top",text:"",weight:2e3},defaultRoutes:{color:"color"},descriptors:{_scriptable:!0,_indexable:!1}};const t1=new WeakMap;var bC={id:"subtitle",start(s,t,e){const a=new bs({ctx:s.ctx,options:e,chart:s});tt.configure(s,a,e),tt.addBox(s,a),t1.set(s,a)},stop(s){tt.removeBox(s,t1.get(s)),t1.delete(s)},beforeUpdate(s,t,e){const a=t1.get(s);tt.configure(s,a,e),a.options=e},defaults:{align:"center",display:!1,font:{weight:"normal"},fullSize:!0,padding:0,position:"top",text:"",weight:1500},defaultRoutes:{color:"color"},descriptors:{_scriptable:!0,_indexable:!1}};const be={average(s){if(!s.length)return!1;let t,e,a=new Set,i=0,n=0;for(t=0,e=s.length;t<e;++t){const h=s[t].element;if(h&&h.hasValue()){const c=h.tooltipPosition();a.add(c.x),i+=c.y,++n}}return n===0||a.size===0?!1:{x:[...a].reduce((h,c)=>h+c)/a.size,y:i/n}},nearest(s,t){if(!s.length)return!1;let e=t.x,a=t.y,i=Number.POSITIVE_INFINITY,n,r,h;for(n=0,r=s.length;n<r;++n){const c=s[n].element;if(c&&c.hasValue()){const l=c.getCenterPoint(),d=q1(t,l);d<i&&(i=d,h=c)}}if(h){const c=h.tooltipPosition();e=c.x,a=c.y}return{x:e,y:a}}};function ft(s,t){return t&&(Z(t)?Array.prototype.push.apply(s,t):s.push(t)),s}function yt(s){return(typeof s=="string"||s instanceof String)&&s.indexOf(`
`)>-1?s.split(`
`):s}function wC(s,t){const{element:e,datasetIndex:a,index:i}=t,n=s.getDatasetMeta(a).controller,{label:r,value:h}=n.getLabelAndValue(i);return{chart:s,label:r,parsed:n.getParsed(i),raw:s.data.datasets[a].data[i],formattedValue:h,dataset:n.getDataset(),dataIndex:i,datasetIndex:a,element:e}}function k2(s,t){const e=s.chart.ctx,{body:a,footer:i,title:n}=s,{boxWidth:r,boxHeight:h}=t,c=G(t.bodyFont),l=G(t.titleFont),d=G(t.footerFont),p=n.length,g=i.length,u=a.length,f=et(t.padding);let v=f.height,x=0,m=a.reduce((w,y)=>w+y.before.length+y.lines.length+y.after.length,0);if(m+=s.beforeBody.length+s.afterBody.length,p&&(v+=p*l.lineHeight+(p-1)*t.titleSpacing+t.titleMarginBottom),m){const w=t.displayColors?Math.max(h,c.lineHeight):c.lineHeight;v+=u*w+(m-u)*c.lineHeight+(m-1)*t.bodySpacing}g&&(v+=t.footerMarginTop+g*d.lineHeight+(g-1)*t.footerSpacing);let M=0;const b=function(w){x=Math.max(x,e.measureText(w).width+M)};return e.save(),e.font=l.string,E(s.title,b),e.font=c.string,E(s.beforeBody.concat(s.afterBody),b),M=t.displayColors?r+2+t.boxPadding:0,E(a,w=>{E(w.before,b),E(w.lines,b),E(w.after,b)}),M=0,e.font=d.string,E(s.footer,b),e.restore(),x+=f.width,{width:x,height:v}}function _C(s,t){const{y:e,height:a}=t;return e<a/2?"top":e>s.height-a/2?"bottom":"center"}function kC(s,t,e,a){const{x:i,width:n}=a,r=e.caretSize+e.caretPadding;if(s==="left"&&i+n+r>t.width||s==="right"&&i-n-r<0)return!0}function CC(s,t,e,a){const{x:i,width:n}=e,{width:r,chartArea:{left:h,right:c}}=s;let l="center";return a==="center"?l=i<=(h+c)/2?"left":"right":i<=n/2?l="left":i>=r-n/2&&(l="right"),kC(l,s,t,e)&&(l="center"),l}function C2(s,t,e){const a=e.yAlign||t.yAlign||_C(s,e);return{xAlign:e.xAlign||t.xAlign||CC(s,t,e,a),yAlign:a}}function SC(s,t){let{x:e,width:a}=s;return t==="right"?e-=a:t==="center"&&(e-=a/2),e}function LC(s,t,e){let{y:a,height:i}=s;return t==="top"?a+=e:t==="bottom"?a-=i+e:a-=i/2,a}function S2(s,t,e,a){const{caretSize:i,caretPadding:n,cornerRadius:r}=s,{xAlign:h,yAlign:c}=e,l=i+n,{topLeft:d,topRight:p,bottomLeft:g,bottomRight:u}=jt(r);let f=SC(t,h);const v=LC(t,c,l);return c==="center"?h==="left"?f+=l:h==="right"&&(f-=l):h==="left"?f-=Math.max(d,g)+i:h==="right"&&(f+=Math.max(p,u)+i),{x:X(f,0,a.width-t.width),y:X(v,0,a.height-t.height)}}function e1(s,t,e){const a=et(e.padding);return t==="center"?s.x+s.width/2:t==="right"?s.x+s.width-a.right:s.x+a.left}function L2(s){return ft([],yt(s))}function AC(s,t,e){return Ft(s,{tooltip:t,tooltipItems:e,type:"tooltip"})}function A2(s,t){const e=t&&t.dataset&&t.dataset.tooltip&&t.dataset.tooltip.callbacks;return e?s.override(e):s}const $i={beforeTitle:mt,title(s){if(s.length>0){const t=s[0],e=t.chart.data.labels,a=e?e.length:0;if(this&&this.options&&this.options.mode==="dataset")return t.dataset.label||"";if(t.label)return t.label;if(a>0&&t.dataIndex<a)return e[t.dataIndex]}return""},afterTitle:mt,beforeBody:mt,beforeLabel:mt,label(s){if(this&&this.options&&this.options.mode==="dataset")return s.label+": "+s.formattedValue||s.formattedValue;let t=s.dataset.label||"";t&&(t+=": ");const e=s.formattedValue;return F(e)||(t+=e),t},labelColor(s){const e=s.chart.getDatasetMeta(s.datasetIndex).controller.getStyle(s.dataIndex);return{borderColor:e.borderColor,backgroundColor:e.backgroundColor,borderWidth:e.borderWidth,borderDash:e.borderDash,borderDashOffset:e.borderDashOffset,borderRadius:0}},labelTextColor(){return this.options.bodyColor},labelPointStyle(s){const e=s.chart.getDatasetMeta(s.datasetIndex).controller.getStyle(s.dataIndex);return{pointStyle:e.pointStyle,rotation:e.rotation}},afterLabel:mt,afterBody:mt,beforeFooter:mt,footer:mt,afterFooter:mt};function st(s,t,e,a){const i=s[t].call(e,a);return typeof i>"u"?$i[t].call(e,a):i}class ss extends dt{constructor(t){super(),this.opacity=0,this._active=[],this._eventPosition=void 0,this._size=void 0,this._cachedAnimations=void 0,this._tooltipItems=[],this.$animations=void 0,this.$context=void 0,this.chart=t.chart,this.options=t.options,this.dataPoints=void 0,this.title=void 0,this.beforeBody=void 0,this.body=void 0,this.afterBody=void 0,this.footer=void 0,this.xAlign=void 0,this.yAlign=void 0,this.x=void 0,this.y=void 0,this.height=void 0,this.width=void 0,this.caretX=void 0,this.caretY=void 0,this.labelColors=void 0,this.labelPointStyles=void 0,this.labelTextColors=void 0}initialize(t){this.options=t,this._cachedAnimations=void 0,this.$context=void 0}_resolveAnimations(){const t=this._cachedAnimations;if(t)return t;const e=this.chart,a=this.options.setContext(this.getContext()),i=a.enabled&&e.options.animation&&a.animations,n=new xi(this.chart,i);return i._cacheable&&(this._cachedAnimations=Object.freeze(n)),n}getContext(){return this.$context||(this.$context=AC(this.chart.getContext(),this,this._tooltipItems))}getTitle(t,e){const{callbacks:a}=e,i=st(a,"beforeTitle",this,t),n=st(a,"title",this,t),r=st(a,"afterTitle",this,t);let h=[];return h=ft(h,yt(i)),h=ft(h,yt(n)),h=ft(h,yt(r)),h}getBeforeBody(t,e){return L2(st(e.callbacks,"beforeBody",this,t))}getBody(t,e){const{callbacks:a}=e,i=[];return E(t,n=>{const r={before:[],lines:[],after:[]},h=A2(a,n);ft(r.before,yt(st(h,"beforeLabel",this,n))),ft(r.lines,st(h,"label",this,n)),ft(r.after,yt(st(h,"afterLabel",this,n))),i.push(r)}),i}getAfterBody(t,e){return L2(st(e.callbacks,"afterBody",this,t))}getFooter(t,e){const{callbacks:a}=e,i=st(a,"beforeFooter",this,t),n=st(a,"footer",this,t),r=st(a,"afterFooter",this,t);let h=[];return h=ft(h,yt(i)),h=ft(h,yt(n)),h=ft(h,yt(r)),h}_createItems(t){const e=this._active,a=this.chart.data,i=[],n=[],r=[];let h=[],c,l;for(c=0,l=e.length;c<l;++c)h.push(wC(this.chart,e[c]));return t.filter&&(h=h.filter((d,p,g)=>t.filter(d,p,g,a))),t.itemSort&&(h=h.sort((d,p)=>t.itemSort(d,p,a))),E(h,d=>{const p=A2(t.callbacks,d);i.push(st(p,"labelColor",this,d)),n.push(st(p,"labelPointStyle",this,d)),r.push(st(p,"labelTextColor",this,d))}),this.labelColors=i,this.labelPointStyles=n,this.labelTextColors=r,this.dataPoints=h,h}update(t,e){const a=this.options.setContext(this.getContext()),i=this._active;let n,r=[];if(!i.length)this.opacity!==0&&(n={opacity:0});else{const h=be[a.position].call(this,i,this._eventPosition);r=this._createItems(a),this.title=this.getTitle(r,a),this.beforeBody=this.getBeforeBody(r,a),this.body=this.getBody(r,a),this.afterBody=this.getAfterBody(r,a),this.footer=this.getFooter(r,a);const c=this._size=k2(this,a),l=Object.assign({},h,c),d=C2(this.chart,a,l),p=S2(a,l,d,this.chart);this.xAlign=d.xAlign,this.yAlign=d.yAlign,n={opacity:1,x:p.x,y:p.y,width:c.width,height:c.height,caretX:h.x,caretY:h.y}}this._tooltipItems=r,this.$context=void 0,n&&this._resolveAnimations().update(this,n),t&&a.external&&a.external.call(this,{chart:this.chart,tooltip:this,replay:e})}drawCaret(t,e,a,i){const n=this.getCaretPosition(t,a,i);e.lineTo(n.x1,n.y1),e.lineTo(n.x2,n.y2),e.lineTo(n.x3,n.y3)}getCaretPosition(t,e,a){const{xAlign:i,yAlign:n}=this,{caretSize:r,cornerRadius:h}=a,{topLeft:c,topRight:l,bottomLeft:d,bottomRight:p}=jt(h),{x:g,y:u}=t,{width:f,height:v}=e;let x,m,M,b,w,y;return n==="center"?(w=u+v/2,i==="left"?(x=g,m=x-r,b=w+r,y=w-r):(x=g+f,m=x+r,b=w-r,y=w+r),M=x):(i==="left"?m=g+Math.max(c,d)+r:i==="right"?m=g+f-Math.max(l,p)-r:m=this.caretX,n==="top"?(b=u,w=b-r,x=m-r,M=m+r):(b=u+v,w=b+r,x=m+r,M=m-r),y=b),{x1:x,x2:m,x3:M,y1:b,y2:w,y3:y}}drawTitle(t,e,a){const i=this.title,n=i.length;let r,h,c;if(n){const l=se(a.rtl,this.x,this.width);for(t.x=e1(this,a.titleAlign,a),e.textAlign=l.textAlign(a.titleAlign),e.textBaseline="middle",r=G(a.titleFont),h=a.titleSpacing,e.fillStyle=a.titleColor,e.font=r.string,c=0;c<n;++c)e.fillText(i[c],l.x(t.x),t.y+r.lineHeight/2),t.y+=r.lineHeight+h,c+1===n&&(t.y+=a.titleMarginBottom-h)}}_drawColorBox(t,e,a,i,n){const r=this.labelColors[a],h=this.labelPointStyles[a],{boxHeight:c,boxWidth:l}=n,d=G(n.bodyFont),p=e1(this,"left",n),g=i.x(p),u=c<d.lineHeight?(d.lineHeight-c)/2:0,f=e.y+u;if(n.usePointStyle){const v={radius:Math.min(l,c)/2,pointStyle:h.pointStyle,rotation:h.rotation,borderWidth:1},x=i.leftForLtr(g,l)+l/2,m=f+c/2;t.strokeStyle=n.multiKeyBackground,t.fillStyle=n.multiKeyBackground,X1(t,v,x,m),t.strokeStyle=r.borderColor,t.fillStyle=r.backgroundColor,X1(t,v,x,m)}else{t.lineWidth=T(r.borderWidth)?Math.max(...Object.values(r.borderWidth)):r.borderWidth||1,t.strokeStyle=r.borderColor,t.setLineDash(r.borderDash||[]),t.lineDashOffset=r.borderDashOffset||0;const v=i.leftForLtr(g,l),x=i.leftForLtr(i.xPlus(g,1),l-2),m=jt(r.borderRadius);Object.values(m).some(M=>M!==0)?(t.beginPath(),t.fillStyle=n.multiKeyBackground,Oe(t,{x:v,y:f,w:l,h:c,radius:m}),t.fill(),t.stroke(),t.fillStyle=r.backgroundColor,t.beginPath(),Oe(t,{x,y:f+1,w:l-2,h:c-2,radius:m}),t.fill()):(t.fillStyle=n.multiKeyBackground,t.fillRect(v,f,l,c),t.strokeRect(v,f,l,c),t.fillStyle=r.backgroundColor,t.fillRect(x,f+1,l-2,c-2))}t.fillStyle=this.labelTextColors[a]}drawBody(t,e,a){const{body:i}=this,{bodySpacing:n,bodyAlign:r,displayColors:h,boxHeight:c,boxWidth:l,boxPadding:d}=a,p=G(a.bodyFont);let g=p.lineHeight,u=0;const f=se(a.rtl,this.x,this.width),v=function(S){e.fillText(S,f.x(t.x+u),t.y+g/2),t.y+=g+n},x=f.textAlign(r);let m,M,b,w,y,k,C;for(e.textAlign=r,e.textBaseline="middle",e.font=p.string,t.x=e1(this,x,a),e.fillStyle=a.bodyColor,E(this.beforeBody,v),u=h&&x!=="right"?r==="center"?l/2+d:l+2+d:0,w=0,k=i.length;w<k;++w){for(m=i[w],M=this.labelTextColors[w],e.fillStyle=M,E(m.before,v),b=m.lines,h&&b.length&&(this._drawColorBox(e,t,w,f,a),g=Math.max(p.lineHeight,c)),y=0,C=b.length;y<C;++y)v(b[y]),g=p.lineHeight;E(m.after,v)}u=0,g=p.lineHeight,E(this.afterBody,v),t.y-=n}drawFooter(t,e,a){const i=this.footer,n=i.length;let r,h;if(n){const c=se(a.rtl,this.x,this.width);for(t.x=e1(this,a.footerAlign,a),t.y+=a.footerMarginTop,e.textAlign=c.textAlign(a.footerAlign),e.textBaseline="middle",r=G(a.footerFont),e.fillStyle=a.footerColor,e.font=r.string,h=0;h<n;++h)e.fillText(i[h],c.x(t.x),t.y+r.lineHeight/2),t.y+=r.lineHeight+a.footerSpacing}}drawBackground(t,e,a,i){const{xAlign:n,yAlign:r}=this,{x:h,y:c}=t,{width:l,height:d}=a,{topLeft:p,topRight:g,bottomLeft:u,bottomRight:f}=jt(i.cornerRadius);e.fillStyle=i.backgroundColor,e.strokeStyle=i.borderColor,e.lineWidth=i.borderWidth,e.beginPath(),e.moveTo(h+p,c),r==="top"&&this.drawCaret(t,e,a,i),e.lineTo(h+l-g,c),e.quadraticCurveTo(h+l,c,h+l,c+g),r==="center"&&n==="right"&&this.drawCaret(t,e,a,i),e.lineTo(h+l,c+d-f),e.quadraticCurveTo(h+l,c+d,h+l-f,c+d),r==="bottom"&&this.drawCaret(t,e,a,i),e.lineTo(h+u,c+d),e.quadraticCurveTo(h,c+d,h,c+d-u),r==="center"&&n==="left"&&this.drawCaret(t,e,a,i),e.lineTo(h,c+p),e.quadraticCurveTo(h,c,h+p,c),e.closePath(),e.fill(),i.borderWidth>0&&e.stroke()}_updateAnimationTarget(t){const e=this.chart,a=this.$animations,i=a&&a.x,n=a&&a.y;if(i||n){const r=be[t.position].call(this,this._active,this._eventPosition);if(!r)return;const h=this._size=k2(this,t),c=Object.assign({},r,this._size),l=C2(e,t,c),d=S2(t,c,l,e);(i._to!==d.x||n._to!==d.y)&&(this.xAlign=l.xAlign,this.yAlign=l.yAlign,this.width=h.width,this.height=h.height,this.caretX=r.x,this.caretY=r.y,this._resolveAnimations().update(this,d))}}_willRender(){return!!this.opacity}draw(t){const e=this.options.setContext(this.getContext());let a=this.opacity;if(!a)return;this._updateAnimationTarget(e);const i={width:this.width,height:this.height},n={x:this.x,y:this.y};a=Math.abs(a)<.001?0:a;const r=et(e.padding),h=this.title.length||this.beforeBody.length||this.body.length||this.afterBody.length||this.footer.length;e.enabled&&h&&(t.save(),t.globalAlpha=a,this.drawBackground(n,t,i,e),di(t,e.textDirection),n.y+=r.top,this.drawTitle(n,t,e),this.drawBody(n,t,e),this.drawFooter(n,t,e),pi(t,e.textDirection),t.restore())}getActiveElements(){return this._active||[]}setActiveElements(t,e){const a=this._active,i=t.map(({datasetIndex:h,index:c})=>{const l=this.chart.getDatasetMeta(h);if(!l)throw new Error("Cannot find a dataset at index "+h);return{datasetIndex:h,element:l.data[c],index:c}}),n=!p1(a,i),r=this._positionChanged(i,e);(n||r)&&(this._active=i,this._eventPosition=e,this._ignoreReplayEvents=!0,this.update(!0))}handleEvent(t,e,a=!0){if(e&&this._ignoreReplayEvents)return!1;this._ignoreReplayEvents=!1;const i=this.options,n=this._active||[],r=this._getActiveElements(t,n,e,a),h=this._positionChanged(r,t),c=e||!p1(r,n)||h;return c&&(this._active=r,(i.enabled||i.external)&&(this._eventPosition={x:t.x,y:t.y},this.update(!0,e))),c}_getActiveElements(t,e,a,i){const n=this.options;if(t.type==="mouseout")return[];if(!i)return e.filter(h=>this.chart.data.datasets[h.datasetIndex]&&this.chart.getDatasetMeta(h.datasetIndex).controller.getParsed(h.index)!==void 0);const r=this.chart.getElementsAtEventForMode(t,n.mode,n,a);return n.reverse&&r.reverse(),r}_positionChanged(t,e){const{caretX:a,caretY:i,options:n}=this,r=be[n.position].call(this,t,e);return r!==!1&&(a!==r.x||i!==r.y)}}_(ss,"positioners",be);var Zi={id:"tooltip",_element:ss,positioners:be,afterInit(s,t,e){e&&(s.tooltip=new ss({chart:s,options:e}))},beforeUpdate(s,t,e){s.tooltip&&s.tooltip.initialize(e)},reset(s,t,e){s.tooltip&&s.tooltip.initialize(e)},afterDraw(s){const t=s.tooltip;if(t&&t._willRender()){const e={tooltip:t};if(s.notifyPlugins("beforeTooltipDraw",{...e,cancelable:!0})===!1)return;t.draw(s.ctx),s.notifyPlugins("afterTooltipDraw",e)}},afterEvent(s,t){if(s.tooltip){const e=t.replay;s.tooltip.handleEvent(t.event,e,t.inChartArea)&&(t.changed=!0)}},defaults:{enabled:!0,external:null,position:"average",backgroundColor:"rgba(0,0,0,0.8)",titleColor:"#fff",titleFont:{weight:"bold"},titleSpacing:2,titleMarginBottom:6,titleAlign:"left",bodyColor:"#fff",bodySpacing:2,bodyFont:{},bodyAlign:"left",footerColor:"#fff",footerSpacing:2,footerMarginTop:6,footerFont:{weight:"bold"},footerAlign:"left",padding:6,caretPadding:2,caretSize:5,cornerRadius:6,boxHeight:(s,t)=>t.bodyFont.size,boxWidth:(s,t)=>t.bodyFont.size,multiKeyBackground:"#fff",displayColors:!0,boxPadding:0,borderColor:"rgba(0,0,0,0)",borderWidth:0,animation:{duration:400,easing:"easeOutQuart"},animations:{numbers:{type:"number",properties:["x","y","width","height","caretX","caretY"]},opacity:{easing:"linear",duration:200}},callbacks:$i},defaultRoutes:{bodyFont:"font",footerFont:"font",titleFont:"font"},descriptors:{_scriptable:s=>s!=="filter"&&s!=="itemSort"&&s!=="external",_indexable:!1,callbacks:{_scriptable:!1,_indexable:!1},animation:{_fallback:!1},animations:{_fallback:"animation"}},additionalOptionScopes:["interaction"]},HC=Object.freeze({__proto__:null,Colors:jk,Decimation:Xk,Filler:Ei,Legend:zi,SubTitle:bC,Title:Ii,Tooltip:Zi});const VC=(s,t,e,a)=>(typeof t=="string"?(e=s.push(t)-1,a.unshift({index:e,label:t})):isNaN(t)&&(e=null),e);function PC(s,t,e,a){const i=s.indexOf(t);if(i===-1)return VC(s,t,e,a);const n=s.lastIndexOf(t);return i!==n?e:i}const DC=(s,t)=>s===null?null:X(Math.round(s),0,t);function H2(s){const t=this.getLabels();return s>=0&&s<t.length?t[s]:s}class M1 extends Yt{constructor(t){super(t),this._startValue=void 0,this._valueRange=0,this._addedLabels=[]}init(t){const e=this._addedLabels;if(e.length){const a=this.getLabels();for(const{index:i,label:n}of e)a[i]===n&&a.splice(i,1);this._addedLabels=[]}super.init(t)}parse(t,e){if(F(t))return null;const a=this.getLabels();return e=isFinite(e)&&a[e]===t?e:PC(a,t,H(e,t),this._addedLabels),DC(e,a.length-1)}determineDataLimits(){const{minDefined:t,maxDefined:e}=this.getUserBounds();let{min:a,max:i}=this.getMinMax(!0);this.options.bounds==="ticks"&&(t||(a=0),e||(i=this.getLabels().length-1)),this.min=a,this.max=i}buildTicks(){const t=this.min,e=this.max,a=this.options.offset,i=[];let n=this.getLabels();n=t===0&&e===n.length-1?n:n.slice(t,e+1),this._valueRange=Math.max(n.length-(a?0:1),1),this._startValue=this.min-(a?.5:0);for(let r=t;r<=e;r++)i.push({value:r});return i}getLabelForValue(t){return H2.call(this,t)}configure(){super.configure(),this.isHorizontal()||(this._reversePixels=!this._reversePixels)}getPixelForValue(t){return typeof t!="number"&&(t=this.parse(t)),t===null?NaN:this.getPixelForDecimal((t-this._startValue)/this._valueRange)}getPixelForTick(t){const e=this.ticks;return t<0||t>e.length-1?null:this.getPixelForValue(e[t].value)}getValueForPixel(t){return Math.round(this._startValue+this.getDecimalForPixel(t)*this._valueRange)}getBasePixel(){return this.bottom}}_(M1,"id","category"),_(M1,"defaults",{ticks:{callback:H2}});function FC(s,t){const e=[],{bounds:i,step:n,min:r,max:h,precision:c,count:l,maxTicks:d,maxDigits:p,includeBounds:g}=s,u=n||1,f=d-1,{min:v,max:x}=t,m=!F(r),M=!F(h),b=!F(l),w=(x-v)/(p+1);let y=ka((x-v)/f/u)*u,k,C,S,L;if(y<1e-14&&!m&&!M)return[{value:v},{value:x}];L=Math.ceil(x/y)-Math.floor(v/y),L>f&&(y=ka(L*y/f/u)*u),F(c)||(k=Math.pow(10,c),y=Math.ceil(y*k)/k),i==="ticks"?(C=Math.floor(v/y)*y,S=Math.ceil(x/y)*y):(C=v,S=x),m&&M&&n&&Hb((h-r)/n,y/1e3)?(L=Math.round(Math.min((h-r)/y,d)),y=(h-r)/L,C=r,S=h):b?(C=m?r:C,S=M?h:S,L=l-1,y=(S-C)/L):(L=(S-C)/y,Ce(L,Math.round(L),y/1e3)?L=Math.round(L):L=Math.ceil(L));const P=Math.max(Ca(y),Ca(C));k=Math.pow(10,F(c)?P:c),C=Math.round(C*k)/k,S=Math.round(S*k)/k;let D=0;for(m&&(g&&C!==r?(e.push({value:r}),C<r&&D++,Ce(Math.round((C+D*y)*k)/k,r,V2(r,w,s))&&D++):C<r&&D++);D<L;++D){const B=Math.round((C+D*y)*k)/k;if(M&&B>h)break;e.push({value:B})}return M&&g&&S!==h?e.length&&Ce(e[e.length-1].value,h,V2(h,w,s))?e[e.length-1].value=h:e.push({value:h}):(!M||S===h)&&e.push({value:S}),e}function V2(s,t,{horizontal:e,minRotation:a}){const i=ct(a),n=(e?Math.sin(i):Math.cos(i))||.001,r=.75*t*(""+s).length;return Math.min(t/n,r)}class y1 extends Yt{constructor(t){super(t),this.start=void 0,this.end=void 0,this._startValue=void 0,this._endValue=void 0,this._valueRange=0}parse(t,e){return F(t)||(typeof t=="number"||t instanceof Number)&&!isFinite(+t)?null:+t}handleTickRangeOptions(){const{beginAtZero:t}=this.options,{minDefined:e,maxDefined:a}=this.getUserBounds();let{min:i,max:n}=this;const r=c=>i=e?i:c,h=c=>n=a?n:c;if(t){const c=xt(i),l=xt(n);c<0&&l<0?h(0):c>0&&l>0&&r(0)}if(i===n){let c=n===0?1:Math.abs(n*.05);h(n+c),t||r(i-c)}this.min=i,this.max=n}getTickLimit(){const t=this.options.ticks;let{maxTicksLimit:e,stepSize:a}=t,i;return a?(i=Math.ceil(this.max/a)-Math.floor(this.min/a)+1,i>1e3&&(console.warn(`scales.${this.id}.ticks.stepSize: ${a} would result generating up to ${i} ticks. Limiting to 1000.`),i=1e3)):(i=this.computeTickLimit(),e=e||11),e&&(i=Math.min(e,i)),i}computeTickLimit(){return Number.POSITIVE_INFINITY}buildTicks(){const t=this.options,e=t.ticks;let a=this.getTickLimit();a=Math.max(2,a);const i={maxTicks:a,bounds:t.bounds,min:t.min,max:t.max,precision:e.precision,step:e.stepSize,count:e.count,maxDigits:this._maxDigits(),horizontal:this.isHorizontal(),minRotation:e.minRotation||0,includeBounds:e.includeBounds!==!1},n=this._range||this,r=FC(i,n);return t.bounds==="ticks"&&G2(r,this,"value"),t.reverse?(r.reverse(),this.start=this.max,this.end=this.min):(this.start=this.min,this.end=this.max),r}configure(){const t=this.ticks;let e=this.min,a=this.max;if(super.configure(),this.options.offset&&t.length){const i=(a-e)/Math.max(t.length-1,1)/2;e-=i,a+=i}this._startValue=e,this._endValue=a,this._valueRange=a-e}getLabelForValue(t){return $e(t,this.chart.options.locale,this.options.ticks.format)}}class b1 extends y1{determineDataLimits(){const{min:t,max:e}=this.getMinMax(!0);this.min=N(t)?t:0,this.max=N(e)?e:1,this.handleTickRangeOptions()}computeTickLimit(){const t=this.isHorizontal(),e=t?this.width:this.height,a=ct(this.options.ticks.minRotation),i=(t?Math.sin(a):Math.cos(a))||.001,n=this._resolveTickFontOptions(0);return Math.ceil(e/Math.min(40,n.lineHeight/i))}getPixelForValue(t){return t===null?NaN:this.getPixelForDecimal((t-this._startValue)/this._valueRange)}getValueForPixel(t){return this._startValue+this.getDecimalForPixel(t)*this._valueRange}}_(b1,"id","linear"),_(b1,"defaults",{ticks:{callback:w1.formatters.numeric}});const Re=s=>Math.floor(Lt(s)),zt=(s,t)=>Math.pow(10,Re(s)+t);function P2(s){return s/Math.pow(10,Re(s))===1}function D2(s,t,e){const a=Math.pow(10,e),i=Math.floor(s/a);return Math.ceil(t/a)-i}function TC(s,t){const e=t-s;let a=Re(e);for(;D2(s,t,a)>10;)a++;for(;D2(s,t,a)<10;)a--;return Math.min(a,Re(s))}function BC(s,{min:t,max:e}){t=ot(s.min,t);const a=[],i=Re(t);let n=TC(t,e),r=n<0?Math.pow(10,Math.abs(n)):1;const h=Math.pow(10,n),c=i>n?Math.pow(10,i):0,l=Math.round((t-c)*r)/r,d=Math.floor((t-c)/h/10)*h*10;let p=Math.floor((l-d)/Math.pow(10,n)),g=ot(s.min,Math.round((c+d+p*Math.pow(10,n))*r)/r);for(;g<e;)a.push({value:g,major:P2(g),significand:p}),p>=10?p=p<15?15:20:p++,p>=20&&(n++,p=2,r=n>=0?1:r),g=Math.round((c+d+p*Math.pow(10,n))*r)/r;const u=ot(s.max,g);return a.push({value:u,major:P2(u),significand:p}),a}class as extends Yt{constructor(t){super(t),this.start=void 0,this.end=void 0,this._startValue=void 0,this._valueRange=0}parse(t,e){const a=y1.prototype.parse.apply(this,[t,e]);if(a===0){this._zero=!0;return}return N(a)&&a>0?a:null}determineDataLimits(){const{min:t,max:e}=this.getMinMax(!0);this.min=N(t)?Math.max(0,t):null,this.max=N(e)?Math.max(0,e):null,this.options.beginAtZero&&(this._zero=!0),this._zero&&this.min!==this._suggestedMin&&!N(this._userMin)&&(this.min=t===zt(this.min,0)?zt(this.min,-1):zt(this.min,0)),this.handleTickRangeOptions()}handleTickRangeOptions(){const{minDefined:t,maxDefined:e}=this.getUserBounds();let a=this.min,i=this.max;const n=h=>a=t?a:h,r=h=>i=e?i:h;a===i&&(a<=0?(n(1),r(10)):(n(zt(a,-1)),r(zt(i,1)))),a<=0&&n(zt(i,-1)),i<=0&&r(zt(a,1)),this.min=a,this.max=i}buildTicks(){const t=this.options,e={min:this._userMin,max:this._userMax},a=BC(e,this);return t.bounds==="ticks"&&G2(a,this,"value"),t.reverse?(a.reverse(),this.start=this.max,this.end=this.min):(this.start=this.min,this.end=this.max),a}getLabelForValue(t){return t===void 0?"0":$e(t,this.chart.options.locale,this.options.ticks.format)}configure(){const t=this.min;super.configure(),this._startValue=Lt(t),this._valueRange=Lt(this.max)-Lt(t)}getPixelForValue(t){return(t===void 0||t===0)&&(t=this.min),t===null||isNaN(t)?NaN:this.getPixelForDecimal(t===this.min?0:(Lt(t)-this._startValue)/this._valueRange)}getValueForPixel(t){const e=this.getDecimalForPixel(t);return Math.pow(10,this._startValue+e*this._valueRange)}}_(as,"id","logarithmic"),_(as,"defaults",{ticks:{callback:w1.formatters.logarithmic,major:{enabled:!0}}});function is(s){const t=s.ticks;if(t.display&&s.display){const e=et(t.backdropPadding);return H(t.font&&t.font.size,W.font.size)+e.height}return 0}function OC(s,t,e){return e=Z(e)?e:[e],{w:Ub(s,t.string,e),h:e.length*t.lineHeight}}function F2(s,t,e,a,i){return s===a||s===i?{start:t-e/2,end:t+e/2}:s<a||s>i?{start:t-e,end:t}:{start:t,end:t+e}}function EC(s){const t={l:s.left+s._padding.left,r:s.right-s._padding.right,t:s.top+s._padding.top,b:s.bottom-s._padding.bottom},e=Object.assign({},t),a=[],i=[],n=s._pointLabels.length,r=s.options.pointLabels,h=r.centerPointLabels?O/n:0;for(let c=0;c<n;c++){const l=r.setContext(s.getPointLabelContext(c));i[c]=l.padding;const d=s.getPointPosition(c,s.drawingArea+i[c],h),p=G(l.font),g=OC(s.ctx,p,s._pointLabels[c]);a[c]=g;const u=Q(s.getIndexAngle(c)+h),f=Math.round(ls(u)),v=F2(f,d.x,g.w,0,180),x=F2(f,d.y,g.h,90,270);RC(e,t,u,v,x)}s.setCenterPoint(t.l-e.l,e.r-t.r,t.t-e.t,e.b-t.b),s._pointLabelItems=$C(s,a,i)}function RC(s,t,e,a,i){const n=Math.abs(Math.sin(e)),r=Math.abs(Math.cos(e));let h=0,c=0;a.start<t.l?(h=(t.l-a.start)/n,s.l=Math.min(s.l,t.l-h)):a.end>t.r&&(h=(a.end-t.r)/n,s.r=Math.max(s.r,t.r+h)),i.start<t.t?(c=(t.t-i.start)/r,s.t=Math.min(s.t,t.t-c)):i.end>t.b&&(c=(i.end-t.b)/r,s.b=Math.max(s.b,t.b+c))}function zC(s,t,e){const a=s.drawingArea,{extra:i,additionalAngle:n,padding:r,size:h}=e,c=s.getPointPosition(t,a+i+r,n),l=Math.round(ls(Q(c.angle+U))),d=NC(c.y,h.h,l),p=ZC(l),g=WC(c.x,h.w,p);return{visible:!0,x:c.x,y:d,textAlign:p,left:g,top:d,right:g+h.w,bottom:d+h.h}}function IC(s,t){if(!t)return!0;const{left:e,top:a,right:i,bottom:n}=s;return!(kt({x:e,y:a},t)||kt({x:e,y:n},t)||kt({x:i,y:a},t)||kt({x:i,y:n},t))}function $C(s,t,e){const a=[],i=s._pointLabels.length,n=s.options,{centerPointLabels:r,display:h}=n.pointLabels,c={extra:is(n)/2,additionalAngle:r?O/i:0};let l;for(let d=0;d<i;d++){c.padding=e[d],c.size=t[d];const p=zC(s,d,c);a.push(p),h==="auto"&&(p.visible=IC(p,l),p.visible&&(l=p))}return a}function ZC(s){return s===0||s===180?"center":s<180?"left":"right"}function WC(s,t,e){return e==="right"?s-=t:e==="center"&&(s-=t/2),s}function NC(s,t,e){return e===90||e===270?s-=t/2:(e>270||e<90)&&(s-=t),s}function jC(s,t,e){const{left:a,top:i,right:n,bottom:r}=e,{backdropColor:h}=t;if(!F(h)){const c=jt(t.borderRadius),l=et(t.backdropPadding);s.fillStyle=h;const d=a-l.left,p=i-l.top,g=n-a+l.width,u=r-i+l.height;Object.values(c).some(f=>f!==0)?(s.beginPath(),Oe(s,{x:d,y:p,w:g,h:u,radius:c}),s.fill()):s.fillRect(d,p,g,u)}}function UC(s,t){const{ctx:e,options:{pointLabels:a}}=s;for(let i=t-1;i>=0;i--){const n=s._pointLabelItems[i];if(!n.visible)continue;const r=a.setContext(s.getPointLabelContext(i));jC(e,r,n);const h=G(r.font),{x:c,y:l,textAlign:d}=n;Xt(e,s._pointLabels[i],c,l+h.lineHeight/2,h,{color:r.color,textAlign:d,textBaseline:"middle"})}}function Wi(s,t,e,a){const{ctx:i}=s;if(e)i.arc(s.xCenter,s.yCenter,t,0,I);else{let n=s.getPointPosition(0,t);i.moveTo(n.x,n.y);for(let r=1;r<a;r++)n=s.getPointPosition(r,t),i.lineTo(n.x,n.y)}}function qC(s,t,e,a,i){const n=s.ctx,r=t.circular,{color:h,lineWidth:c}=t;!r&&!a||!h||!c||e<0||(n.save(),n.strokeStyle=h,n.lineWidth=c,n.setLineDash(i.dash||[]),n.lineDashOffset=i.dashOffset,n.beginPath(),Wi(s,e,r,a),n.closePath(),n.stroke(),n.restore())}function GC(s,t,e){return Ft(s,{label:e,index:t,type:"pointLabel"})}class we extends y1{constructor(t){super(t),this.xCenter=void 0,this.yCenter=void 0,this.drawingArea=void 0,this._pointLabels=[],this._pointLabelItems=[]}setDimensions(){const t=this._padding=et(is(this.options)/2),e=this.width=this.maxWidth-t.width,a=this.height=this.maxHeight-t.height;this.xCenter=Math.floor(this.left+e/2+t.left),this.yCenter=Math.floor(this.top+a/2+t.top),this.drawingArea=Math.floor(Math.min(e,a)/2)}determineDataLimits(){const{min:t,max:e}=this.getMinMax(!1);this.min=N(t)&&!isNaN(t)?t:0,this.max=N(e)&&!isNaN(e)?e:0,this.handleTickRangeOptions()}computeTickLimit(){return Math.ceil(this.drawingArea/is(this.options))}generateTickLabels(t){y1.prototype.generateTickLabels.call(this,t),this._pointLabels=this.getLabels().map((e,a)=>{const i=z(this.options.pointLabels.callback,[e,a],this);return i||i===0?i:""}).filter((e,a)=>this.chart.getDataVisibility(a))}fit(){const t=this.options;t.display&&t.pointLabels.display?EC(this):this.setCenterPoint(0,0,0,0)}setCenterPoint(t,e,a,i){this.xCenter+=Math.floor((t-e)/2),this.yCenter+=Math.floor((a-i)/2),this.drawingArea-=Math.min(this.drawingArea/2,Math.max(t,e,a,i))}getIndexAngle(t){const e=I/(this._pointLabels.length||1),a=this.options.startAngle||0;return Q(t*e+ct(a))}getDistanceFromCenterForValue(t){if(F(t))return NaN;const e=this.drawingArea/(this.max-this.min);return this.options.reverse?(this.max-t)*e:(t-this.min)*e}getValueForDistanceFromCenter(t){if(F(t))return NaN;const e=t/(this.drawingArea/(this.max-this.min));return this.options.reverse?this.max-e:this.min+e}getPointLabelContext(t){const e=this._pointLabels||[];if(t>=0&&t<e.length){const a=e[t];return GC(this.getContext(),t,a)}}getPointPosition(t,e,a=0){const i=this.getIndexAngle(t)-U+a;return{x:Math.cos(i)*e+this.xCenter,y:Math.sin(i)*e+this.yCenter,angle:i}}getPointPositionForValue(t,e){return this.getPointPosition(t,this.getDistanceFromCenterForValue(e))}getBasePosition(t){return this.getPointPositionForValue(t||0,this.getBaseValue())}getPointLabelPosition(t){const{left:e,top:a,right:i,bottom:n}=this._pointLabelItems[t];return{left:e,top:a,right:i,bottom:n}}drawBackground(){const{backgroundColor:t,grid:{circular:e}}=this.options;if(t){const a=this.ctx;a.save(),a.beginPath(),Wi(this,this.getDistanceFromCenterForValue(this._endValue),e,this._pointLabels.length),a.closePath(),a.fillStyle=t,a.fill(),a.restore()}}drawGrid(){const t=this.ctx,e=this.options,{angleLines:a,grid:i,border:n}=e,r=this._pointLabels.length;let h,c,l;if(e.pointLabels.display&&UC(this,r),i.display&&this.ticks.forEach((d,p)=>{if(p!==0||p===0&&this.min<0){c=this.getDistanceFromCenterForValue(d.value);const g=this.getContext(p),u=i.setContext(g),f=n.setContext(g);qC(this,u,c,r,f)}}),a.display){for(t.save(),h=r-1;h>=0;h--){const d=a.setContext(this.getPointLabelContext(h)),{color:p,lineWidth:g}=d;!g||!p||(t.lineWidth=g,t.strokeStyle=p,t.setLineDash(d.borderDash),t.lineDashOffset=d.borderDashOffset,c=this.getDistanceFromCenterForValue(e.reverse?this.min:this.max),l=this.getPointPosition(h,c),t.beginPath(),t.moveTo(this.xCenter,this.yCenter),t.lineTo(l.x,l.y),t.stroke())}t.restore()}}drawBorder(){}drawLabels(){const t=this.ctx,e=this.options,a=e.ticks;if(!a.display)return;const i=this.getIndexAngle(0);let n,r;t.save(),t.translate(this.xCenter,this.yCenter),t.rotate(i),t.textAlign="center",t.textBaseline="middle",this.ticks.forEach((h,c)=>{if(c===0&&this.min>=0&&!e.reverse)return;const l=a.setContext(this.getContext(c)),d=G(l.font);if(n=this.getDistanceFromCenterForValue(this.ticks[c].value),l.showLabelBackdrop){t.font=d.string,r=t.measureText(h.label).width,t.fillStyle=l.backdropColor;const p=et(l.backdropPadding);t.fillRect(-r/2-p.left,-n-d.size/2-p.top,r+p.width,d.size+p.height)}Xt(t,h.label,0,-n,d,{color:l.color,strokeColor:l.textStrokeColor,strokeWidth:l.textStrokeWidth})}),t.restore()}drawTitle(){}}_(we,"id","radialLinear"),_(we,"defaults",{display:!0,animate:!0,position:"chartArea",angleLines:{display:!0,lineWidth:1,borderDash:[],borderDashOffset:0},grid:{circular:!1},startAngle:0,ticks:{showLabelBackdrop:!0,callback:w1.formatters.numeric},pointLabels:{backdropColor:void 0,backdropPadding:2,display:!0,font:{size:10},callback(t){return t},padding:5,centerPointLabels:!1}}),_(we,"defaultRoutes",{"angleLines.color":"borderColor","pointLabels.color":"color","ticks.color":"color"}),_(we,"descriptors",{angleLines:{_fallback:"grid"}});const A1={millisecond:{common:!0,size:1,steps:1e3},second:{common:!0,size:1e3,steps:60},minute:{common:!0,size:6e4,steps:60},hour:{common:!0,size:36e5,steps:24},day:{common:!0,size:864e5,steps:30},week:{common:!1,size:6048e5,steps:4},month:{common:!0,size:2628e6,steps:12},quarter:{common:!1,size:7884e6,steps:4},year:{common:!0,size:3154e7}},it=Object.keys(A1);function T2(s,t){return s-t}function B2(s,t){if(F(t))return null;const e=s._adapter,{parser:a,round:i,isoWeekday:n}=s._parseOpts;let r=t;return typeof a=="function"&&(r=a(r)),N(r)||(r=typeof a=="string"?e.parse(r,a):e.parse(r)),r===null?null:(i&&(r=i==="week"&&(ae(n)||n===!0)?e.startOf(r,"isoWeek",n):e.startOf(r,i)),+r)}function O2(s,t,e,a){const i=it.length;for(let n=it.indexOf(s);n<i-1;++n){const r=A1[it[n]],h=r.steps?r.steps:Number.MAX_SAFE_INTEGER;if(r.common&&Math.ceil((e-t)/(h*r.size))<=a)return it[n]}return it[i-1]}function XC(s,t,e,a,i){for(let n=it.length-1;n>=it.indexOf(e);n--){const r=it[n];if(A1[r].common&&s._adapter.diff(i,a,r)>=t-1)return r}return it[e?it.indexOf(e):0]}function YC(s){for(let t=it.indexOf(s)+1,e=it.length;t<e;++t)if(A1[it[t]].common)return it[t]}function E2(s,t,e){if(!e)s[t]=!0;else if(e.length){const{lo:a,hi:i}=ds(e,t),n=e[a]>=t?e[a]:e[i];s[n]=!0}}function KC(s,t,e,a){const i=s._adapter,n=+i.startOf(t[0].value,a),r=t[t.length-1].value;let h,c;for(h=n;h<=r;h=+i.add(h,1,a))c=e[h],c>=0&&(t[c].major=!0);return t}function R2(s,t,e){const a=[],i={},n=t.length;let r,h;for(r=0;r<n;++r)h=t[r],i[h]=r,a.push({value:h,major:!1});return n===0||!e?a:KC(s,a,i,e)}class ze extends Yt{constructor(t){super(t),this._cache={data:[],labels:[],all:[]},this._unit="day",this._majorUnit=void 0,this._offsets={},this._normalized=!1,this._parseOpts=void 0}init(t,e={}){const a=t.time||(t.time={}),i=this._adapter=new c_._date(t.adapters.date);i.init(e),ke(a.displayFormats,i.formats()),this._parseOpts={parser:a.parser,round:a.round,isoWeekday:a.isoWeekday},super.init(t),this._normalized=e.normalized}parse(t,e){return t===void 0?null:B2(this,t)}beforeLayout(){super.beforeLayout(),this._cache={data:[],labels:[],all:[]}}determineDataLimits(){const t=this.options,e=this._adapter,a=t.time.unit||"day";let{min:i,max:n,minDefined:r,maxDefined:h}=this.getUserBounds();function c(l){!r&&!isNaN(l.min)&&(i=Math.min(i,l.min)),!h&&!isNaN(l.max)&&(n=Math.max(n,l.max))}(!r||!h)&&(c(this._getLabelBounds()),(t.bounds!=="ticks"||t.ticks.source!=="labels")&&c(this.getMinMax(!1))),i=N(i)&&!isNaN(i)?i:+e.startOf(Date.now(),a),n=N(n)&&!isNaN(n)?n:+e.endOf(Date.now(),a)+1,this.min=Math.min(i,n-1),this.max=Math.max(i+1,n)}_getLabelBounds(){const t=this.getLabelTimestamps();let e=Number.POSITIVE_INFINITY,a=Number.NEGATIVE_INFINITY;return t.length&&(e=t[0],a=t[t.length-1]),{min:e,max:a}}buildTicks(){const t=this.options,e=t.time,a=t.ticks,i=a.source==="labels"?this.getLabelTimestamps():this._generate();t.bounds==="ticks"&&i.length&&(this.min=this._userMin||i[0],this.max=this._userMax||i[i.length-1]);const n=this.min,r=this.max,h=Fb(i,n,r);return this._unit=e.unit||(a.autoSkip?O2(e.minUnit,this.min,this.max,this._getLabelCapacity(n)):XC(this,h.length,e.minUnit,this.min,this.max)),this._majorUnit=!a.major.enabled||this._unit==="year"?void 0:YC(this._unit),this.initOffsets(i),t.reverse&&h.reverse(),R2(this,h,this._majorUnit)}afterAutoSkip(){this.options.offsetAfterAutoskip&&this.initOffsets(this.ticks.map(t=>+t.value))}initOffsets(t=[]){let e=0,a=0,i,n;this.options.offset&&t.length&&(i=this.getDecimalForValue(t[0]),t.length===1?e=1-i:e=(this.getDecimalForValue(t[1])-i)/2,n=this.getDecimalForValue(t[t.length-1]),t.length===1?a=n:a=(n-this.getDecimalForValue(t[t.length-2]))/2);const r=t.length<3?.5:.25;e=X(e,0,r),a=X(a,0,r),this._offsets={start:e,end:a,factor:1/(e+1+a)}}_generate(){const t=this._adapter,e=this.min,a=this.max,i=this.options,n=i.time,r=n.unit||O2(n.minUnit,e,a,this._getLabelCapacity(e)),h=H(i.ticks.stepSize,1),c=r==="week"?n.isoWeekday:!1,l=ae(c)||c===!0,d={};let p=e,g,u;if(l&&(p=+t.startOf(p,"isoWeek",c)),p=+t.startOf(p,l?"day":r),t.diff(a,e,r)>1e5*h)throw new Error(e+" and "+a+" are too far apart with stepSize of "+h+" "+r);const f=i.ticks.source==="data"&&this.getDataTimestamps();for(g=p,u=0;g<a;g=+t.add(g,h,r),u++)E2(d,g,f);return(g===a||i.bounds==="ticks"||u===1)&&E2(d,g,f),Object.keys(d).sort(T2).map(v=>+v)}getLabelForValue(t){const e=this._adapter,a=this.options.time;return a.tooltipFormat?e.format(t,a.tooltipFormat):e.format(t,a.displayFormats.datetime)}format(t,e){const i=this.options.time.displayFormats,n=this._unit,r=e||i[n];return this._adapter.format(t,r)}_tickFormatFunction(t,e,a,i){const n=this.options,r=n.ticks.callback;if(r)return z(r,[t,e,a],this);const h=n.time.displayFormats,c=this._unit,l=this._majorUnit,d=c&&h[c],p=l&&h[l],g=a[e],u=l&&p&&g&&g.major;return this._adapter.format(t,i||(u?p:d))}generateTickLabels(t){let e,a,i;for(e=0,a=t.length;e<a;++e)i=t[e],i.label=this._tickFormatFunction(i.value,e,t)}getDecimalForValue(t){return t===null?NaN:(t-this.min)/(this.max-this.min)}getPixelForValue(t){const e=this._offsets,a=this.getDecimalForValue(t);return this.getPixelForDecimal((e.start+a)*e.factor)}getValueForPixel(t){const e=this._offsets,a=this.getDecimalForPixel(t)/e.factor-e.end;return this.min+a*(this.max-this.min)}_getLabelSize(t){const e=this.options.ticks,a=this.ctx.measureText(t).width,i=ct(this.isHorizontal()?e.maxRotation:e.minRotation),n=Math.cos(i),r=Math.sin(i),h=this._resolveTickFontOptions(0).size;return{w:a*n+h*r,h:a*r+h*n}}_getLabelCapacity(t){const e=this.options.time,a=e.displayFormats,i=a[e.unit]||a.millisecond,n=this._tickFormatFunction(t,0,R2(this,[t],this._majorUnit),i),r=this._getLabelSize(n),h=Math.floor(this.isHorizontal()?this.width/r.w:this.height/r.h)-1;return h>0?h:1}getDataTimestamps(){let t=this._cache.data||[],e,a;if(t.length)return t;const i=this.getMatchingVisibleMetas();if(this._normalized&&i.length)return this._cache.data=i[0].controller.getAllParsedValues(this);for(e=0,a=i.length;e<a;++e)t=t.concat(i[e].controller.getAllParsedValues(this));return this._cache.data=this.normalize(t)}getLabelTimestamps(){const t=this._cache.labels||[];let e,a;if(t.length)return t;const i=this.getLabels();for(e=0,a=i.length;e<a;++e)t.push(B2(this,i[e]));return this._cache.labels=this._normalized?t:this.normalize(t)}normalize(t){return K2(t.sort(T2))}}_(ze,"id","time"),_(ze,"defaults",{bounds:"data",adapters:{},time:{parser:!1,unit:!1,round:!1,isoWeekday:!1,minUnit:"millisecond",displayFormats:{}},ticks:{source:"auto",callback:!1,major:{enabled:!1}}});function s1(s,t,e){let a=0,i=s.length-1,n,r,h,c;e?(t>=s[a].pos&&t<=s[i].pos&&({lo:a,hi:i}=_t(s,"pos",t)),{pos:n,time:h}=s[a],{pos:r,time:c}=s[i]):(t>=s[a].time&&t<=s[i].time&&({lo:a,hi:i}=_t(s,"time",t)),{time:n,pos:h}=s[a],{time:r,pos:c}=s[i]);const l=r-n;return l?h+(c-h)*(t-n)/l:h}class ns extends ze{constructor(t){super(t),this._table=[],this._minPos=void 0,this._tableRange=void 0}initOffsets(){const t=this._getTimestampsForTable(),e=this._table=this.buildLookupTable(t);this._minPos=s1(e,this.min),this._tableRange=s1(e,this.max)-this._minPos,super.initOffsets(t)}buildLookupTable(t){const{min:e,max:a}=this,i=[],n=[];let r,h,c,l,d;for(r=0,h=t.length;r<h;++r)l=t[r],l>=e&&l<=a&&i.push(l);if(i.length<2)return[{time:e,pos:0},{time:a,pos:1}];for(r=0,h=i.length;r<h;++r)d=i[r+1],c=i[r-1],l=i[r],Math.round((d+c)/2)!==l&&n.push({time:l,pos:r/(h-1)});return n}_generate(){const t=this.min,e=this.max;let a=super.getDataTimestamps();return(!a.includes(t)||!a.length)&&a.splice(0,0,t),(!a.includes(e)||a.length===1)&&a.push(e),a.sort((i,n)=>i-n)}_getTimestampsForTable(){let t=this._cache.all||[];if(t.length)return t;const e=this.getDataTimestamps(),a=this.getLabelTimestamps();return e.length&&a.length?t=this.normalize(e.concat(a)):t=e.length?e:a,t=this._cache.all=t,t}getDecimalForValue(t){return(s1(this._table,t)-this._minPos)/this._tableRange}getValueForPixel(t){const e=this._offsets,a=this.getDecimalForPixel(t)/e.factor-e.end;return s1(this._table,a*this._tableRange+this._minPos,!0)}}_(ns,"id","timeseries"),_(ns,"defaults",ze.defaults);var JC=Object.freeze({__proto__:null,CategoryScale:M1,LinearScale:b1,LogarithmicScale:as,RadialLinearScale:we,TimeScale:ze,TimeSeriesScale:ns});const QC=[h_,Rk,HC,JC];at.register(Ae,Ct,Ve,b1,M1,Ii,Zi,zi,Ei);let Zt=null,Wt=null;const z2=50,gt={labels:[],generation:[],consumption:[]},ut={labels:[],buyPrice:[],sellPrice:[]},Pe={responsive:!0,maintainAspectRatio:!1,animation:!1,interaction:{mode:"index",intersect:!1},plugins:{legend:{position:"top",labels:{usePointStyle:!0,color:"#94a3b8"}},tooltip:{mode:"index",intersect:!1,backgroundColor:"#1e293b",titleColor:"#f8fafc",bodyColor:"#cbd5e1",borderColor:"#334155",borderWidth:1}},scales:{x:{display:!0,grid:{color:"#334155"},ticks:{color:"#94a3b8"}},y:{display:!0,beginAtZero:!0,grid:{color:"#334155"},ticks:{color:"#94a3b8"}}}};function tS(){const s=document.getElementById("energyFlowChart").getContext("2d"),t=s.createLinearGradient(0,0,0,400);t.addColorStop(0,"rgba(16, 185, 129, 0.5)"),t.addColorStop(1,"rgba(16, 185, 129, 0.0)");const e=s.createLinearGradient(0,0,0,400);e.addColorStop(0,"rgba(59, 130, 246, 0.5)"),e.addColorStop(1,"rgba(59, 130, 246, 0.0)"),Zt=new at(s,{type:"line",data:{labels:[],datasets:[{label:"Generation (kWh)",data:[],borderColor:"#10B981",backgroundColor:t,borderWidth:2,fill:!0,tension:.4,pointRadius:0},{label:"Consumption (kWh)",data:[],borderColor:"#3B82F6",backgroundColor:e,borderWidth:2,fill:!0,tension:.4,pointRadius:0}]},options:{...Pe,plugins:{...Pe.plugins,title:{display:!1,text:"Energy Flow"}}}})}function eS(){const s=document.getElementById("marketPriceChart").getContext("2d");Wt=new at(s,{type:"line",data:{labels:[],datasets:[{label:"Buy Price ($)",data:[],borderColor:"#F87171",backgroundColor:"rgba(248, 113, 113, 0.1)",borderWidth:2,fill:!1,tension:.1,stepped:!0,pointRadius:0},{label:"Sell Price ($)",data:[],borderColor:"#34D399",backgroundColor:"rgba(52, 211, 153, 0.1)",borderWidth:2,fill:!1,tension:.1,stepped:!0,pointRadius:0}]},options:{...Pe,scales:{...Pe.scales,y:{...Pe.scales.y,ticks:{callback:function(t){return"$"+t.toFixed(2)},color:"#94a3b8"}}}}})}function sS(s){var a,i;const e=new Date().toLocaleTimeString();gt.labels.push(e),gt.generation.push(s.total_generation||0),gt.consumption.push(s.total_consumption||0),ut.labels.push(e),ut.buyPrice.push(((a=s.market_prices)==null?void 0:a.buy)||0),ut.sellPrice.push(((i=s.market_prices)==null?void 0:i.sell)||0),gt.labels.length>z2&&(gt.labels.shift(),gt.generation.shift(),gt.consumption.shift()),ut.labels.length>z2&&(ut.labels.shift(),ut.buyPrice.shift(),ut.sellPrice.shift()),Zt&&(Zt.data.labels=gt.labels,Zt.data.datasets[0].data=gt.generation,Zt.data.datasets[1].data=gt.consumption,Zt.update("none")),Wt&&(Wt.data.labels=ut.labels,Wt.data.datasets[0].data=ut.buyPrice,Wt.data.datasets[1].data=ut.sellPrice,Wt.update("none"))}function Ni(s){const t="#94a3b8",e="#334155",a=i=>{i&&(i.options.scales.x&&(i.options.scales.x.ticks.color=t,i.options.scales.x.grid.color=e),i.options.scales.y&&(i.options.scales.y.ticks.color=t,i.options.scales.y.grid.color=e),i.options.plugins.legend&&(i.options.plugins.legend.labels.color=t),i.update())};a(Zt),a(Wt)}function aS(){document.documentElement.classList.add("dark"),Ni()}function iS(){document.documentElement.classList.add("dark"),Ni()}function V(s,t="info"){const e=document.getElementById("status-message"),a=document.getElementById("status-message-text"),i={success:"bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",error:"bg-red-500/20 text-red-400 border border-red-500/30",warning:"bg-amber-500/20 text-amber-400 border border-amber-500/30",info:"bg-blue-500/20 text-blue-400 border border-blue-500/30"};e.className="hidden ml-auto flex items-center gap-3 px-3 py-1 rounded-lg text-sm transition-all",e.classList.add(...i[t].split(" ")),e.classList.remove("hidden"),a&&(a.textContent=s),setTimeout(()=>{e.classList.add("hidden")},5e3)}function re(s){const t=document.getElementById("start-btn"),e=document.getElementById("stop-btn"),a=document.getElementById("pause-btn"),i=document.getElementById("resume-btn"),n=document.getElementById("update-meters-btn"),r=document.getElementById("meter-count");s.running?(t&&(t.disabled=!0),e&&(e.disabled=!1),n&&(n.disabled=!0),r&&(r.disabled=!0),s.paused?(a&&(a.disabled=!0,a.classList.add("hidden")),i&&(i.disabled=!1,i.classList.remove("hidden"))):(a&&(a.disabled=!1,a.classList.remove("hidden")),i&&(i.disabled=!0,i.classList.add("hidden")))):(t&&(t.disabled=!1),e&&(e.disabled=!0),a&&(a.disabled=!0,a.classList.add("hidden")),i&&(i.disabled=!0,i.classList.add("hidden")),n&&(n.disabled=!1),r&&(r.disabled=!1)),s.num_meters&&r&&(r.value=s.num_meters)}let q=[],_e={gen:0,cons:0,surplus:0,traders:0};const ws=new Map;let _s=1,ji=20,Ui="card";function nS(s){const t=q.findIndex(e=>e.meter_id===s.meter_id);ws.set(s.meter_id,Date.now()),t!==-1?q[t]=s:q.push(s)}function oS(s){const t=q.findIndex(e=>e.meter_id===s);t!==-1&&q.splice(t,1),ws.delete(s)}function rS(s){_e=s}function qi(s){const t=ws.get(s);return t?Date.now()-t<3e4:!1}function ks(){return _s}function Gi(s){_s=s}function Xi(){return ji}function hS(s){ji=s,_s=1}function cS(){return Ui}function lS(s){Ui=s}function dS(s,t=""){const e=(s.surplus_energy||0)>0,a=(s.deficit_energy||0)>0,i=qi(s.meter_id),n=s.battery_level||0,r={Solar_Prosumer:{bg:"bg-gradient-to-r from-amber-500/20 to-orange-500/10",border:"border-amber-500/30",text:"text-amber-400",label:"Solar",icon:'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>'},Grid_Consumer:{bg:"bg-gradient-to-r from-blue-500/20 to-cyan-500/10",border:"border-blue-500/30",text:"text-blue-400",label:"Consumer",icon:'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>'},Hybrid_Prosumer:{bg:"bg-gradient-to-r from-purple-500/20 to-pink-500/10",border:"border-purple-500/30",text:"text-purple-400",label:"Hybrid",icon:'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/></svg>'},Battery_Storage:{bg:"bg-gradient-to-r from-emerald-500/20 to-teal-500/10",border:"border-emerald-500/30",text:"text-emerald-400",label:"Storage",icon:'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/></svg>'}},h=r[s.meter_type]||r.Grid_Consumer,c=n>60?"from-emerald-400 to-green-500":n>30?"from-amber-400 to-yellow-500":"from-red-400 to-orange-500";return`
        <article class="group relative w-full rounded-2xl border ${e?"bg-emerald-500/5 border-emerald-500/20":a?"bg-orange-500/5 border-orange-500/20":"bg-slate-800/30 border-slate-700/30"} bg-slate-900/40 backdrop-blur-sm shadow-lg hover:shadow-xl hover:shadow-slate-900/50 transition-all duration-300 overflow-hidden" id="${t}card-${s.meter_id}">
            
            <!-- Glow effect for live meters -->
            ${i?'<div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent pointer-events-none"></div>':""}
            
            <!-- Header -->
            <header class="relative px-4 pt-4 pb-3 flex items-start justify-between gap-2">
                <div class="flex items-center gap-2.5 min-w-0 flex-1">
                    <!-- Type Badge -->
                    <div class="flex-shrink-0 flex h-9 w-9 items-center justify-center rounded-xl ${h.bg} ${h.border} border">
                        <span class="${h.text}">${h.icon}</span>
                    </div>
                    <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-2">
                            <h2 class="text-sm font-semibold text-white truncate" title="${s.meter_id}">${s.meter_id}</h2>
                            <span class="flex-shrink-0 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${h.bg} ${h.text}">
                                ${h.label}
                            </span>
                        </div>
                        <p class="text-[10px] text-slate-500 truncate" title="${s.location}">${s.location||"Unknown location"}</p>
                    </div>
                </div>
                
                <!-- Status & Actions -->
                <div class="flex items-center gap-1.5 flex-shrink-0">
                    <span class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wide ${i?"bg-emerald-500/15 text-emerald-400 animate-pulse":"bg-slate-700/50 text-slate-500"}">
                        <span class="h-1.5 w-1.5 rounded-full ${i?"bg-emerald-400":"bg-slate-500"}"></span>
                        ${i?"LIVE":"IDLE"}
                    </span>
                    <button onclick="window.openMeterDetails('${s.meter_id}')" class="p-1.5 text-slate-500 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        </svg>
                    </button>
                </div>
            </header>

            <!-- Energy Stats - Main Focus -->
            <div id="${t}auto-${s.meter_id}" class="px-4 pb-4 space-y-3">
                <div class="grid grid-cols-2 gap-2">
                    <!-- Generation -->
                    <div class="relative overflow-hidden rounded-xl bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-transparent p-3 border border-amber-500/10">
                        <div class="flex items-center gap-1.5 mb-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-400">
                                <circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/>
                            </svg>
                            <span class="text-[10px] font-medium text-amber-400/80 uppercase tracking-wider">Gen</span>
                        </div>
                        <p class="flex items-baseline gap-0.5">
                            <span class="text-xl font-bold tracking-tight text-white tabular-nums val-gen transition-all duration-300">${(s.energy_generated||0).toFixed(1)}</span>
                            <span class="text-[10px] font-medium text-slate-500">kWh</span>
                        </p>
                    </div>

                    <!-- Consumption -->
                    <div class="relative overflow-hidden rounded-xl bg-gradient-to-br from-blue-500/10 via-blue-500/5 to-transparent p-3 border border-blue-500/10">
                        <div class="flex items-center gap-1.5 mb-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-blue-400">
                                <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
                            </svg>
                            <span class="text-[10px] font-medium text-blue-400/80 uppercase tracking-wider">Use</span>
                        </div>
                        <p class="flex items-baseline gap-0.5">
                            <span class="text-xl font-bold tracking-tight text-white tabular-nums val-cons transition-all duration-300">${(s.energy_consumed||0).toFixed(1)}</span>
                            <span class="text-[10px] font-medium text-slate-500">kWh</span>
                        </p>
                    </div>
                </div>

                <!-- Battery + Metrics Row -->
                <div class="flex items-center gap-3 px-0.5">
                    <!-- Battery -->
                    <div class="flex items-center gap-2 flex-1">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500 flex-shrink-0">
                            <rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/>
                        </svg>
                        <div class="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                            <div class="h-full rounded-full bg-gradient-to-r ${c} transition-all duration-500 val-batt-bar" style="width: ${Math.max(n,3)}%"></div>
                        </div>
                        <span class="text-xs font-semibold tabular-nums text-slate-400 val-batt-text w-10 text-right">${n.toFixed(0)}%</span>
                    </div>
                    
                    <!-- Temp -->
                    <div class="flex items-center gap-1.5 px-2 py-1 bg-slate-800/50 rounded-lg">
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-400">
                            <path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>
                        </svg>
                        <span class="text-[11px] font-medium tabular-nums text-slate-400 val-temp">${(s.temperature||0).toFixed(0)}°</span>
                    </div>
                </div>

                <!-- Trading Status -->
                <div class="status-container mt-auto">
                    ${e?`
                        <div class="group/status flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/15 transition-colors">
                            <div class="flex items-center gap-3">
                                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 group-hover/status:scale-110 transition-transform">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>
                                    </svg>
                                </div>
                                <div>
                                    <span class="block text-[10px] font-bold text-emerald-400 uppercase tracking-wider leading-none mb-1">Selling</span>
                                    <span class="text-xs text-slate-300 font-medium">${(s.surplus_energy||0).toFixed(2)} kWh</span>
                                </div>
                            </div>
                            <div class="text-right">
                                <span class="block text-[10px] font-medium text-emerald-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                                <span class="text-base font-bold text-emerald-400">$${(s.max_sell_price||0).toFixed(2)}</span>
                            </div>
                        </div>
                    `:""}
                    ${a?`
                        <div class="group/status flex items-center justify-between p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/15 transition-colors">
                            <div class="flex items-center gap-3">
                                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400 group-hover/status:scale-110 transition-transform">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>
                                    </svg>
                                </div>
                                <div>
                                    <span class="block text-[10px] font-bold text-amber-400 uppercase tracking-wider leading-none mb-1">Buying</span>
                                    <span class="text-xs text-slate-300 font-medium">${(s.deficit_energy||0).toFixed(2)} kWh</span>
                                </div>
                            </div>
                            <div class="text-right">
                                <span class="block text-[10px] font-medium text-amber-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                                <span class="text-base font-bold text-amber-400">$${(s.max_buy_price||0).toFixed(2)}</span>
                            </div>
                        </div>
                    `:""}
                    ${!e&&!a?`
                        <div class="flex items-center justify-center gap-2 py-3 px-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500">
                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                            </svg>
                            <span class="text-xs text-slate-500 font-medium">System Balanced</span>
                        </div>
                    `:""}
                </div>
            </div>

            <!-- Manual Mode Controls (Hidden by default) -->
            <div id="${t}manual-${s.meter_id}" class="hidden px-4 pb-4 space-y-3">
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Gen (kWh)</label>
                        <input type="number" id="${t}gen-${s.meter_id}" step="0.01" min="0" 
                               value="${(s.energy_generated||0).toFixed(2)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Use (kWh)</label>
                        <input type="number" id="${t}cons-${s.meter_id}" step="0.01" min="0" 
                               value="${(s.energy_consumed||0).toFixed(2)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Battery %</label>
                        <input type="number" id="${t}batt-${s.meter_id}" step="1" min="0" max="100" 
                               value="${n.toFixed(0)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Temp (°C)</label>
                        <input type="number" id="${t}temp-${s.meter_id}" step="0.1" 
                               value="${(s.temperature||25).toFixed(1)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-2">
                     <button onclick="window.applyManualValues('${s.meter_id}', '${t}')" 
                            class="px-3 py-1.5 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                        Apply
                    </button>
                    <button onclick="window.resetToAuto('${s.meter_id}', '${t}')" 
                            class="px-3 py-1.5 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                        Reset
                    </button>
                </div>
                
                <!-- Hidden inputs for extra fields -->
                <input type="hidden" id="${t}volt-${s.meter_id}" value="${(s.voltage||240).toFixed(1)}">
                <input type="hidden" id="${t}curr-${s.meter_id}" value="${(s.current||0).toFixed(3)}">
                <input type="hidden" id="${t}freq-${s.meter_id}" value="${(s.frequency||50).toFixed(2)}">
                <input type="hidden" id="${t}sell-${s.meter_id}" value="${(s.max_sell_price||.12).toFixed(2)}">
                <input type="hidden" id="${t}buy-${s.meter_id}" value="${(s.max_buy_price||.28).toFixed(2)}">
            </div>

            <!-- Footer Actions -->
            <footer class="grid grid-cols-2 gap-2 px-4 py-3 border-t border-slate-800/80 bg-slate-900/30">
                <button onclick="window.toggleManualMode('${s.meter_id}', '${t}')" 
                        id="${t}mode-btn-${s.meter_id}"
                        class="flex items-center justify-center gap-2 text-slate-400 hover:text-white hover:bg-slate-800 px-3 py-2 rounded-xl text-xs font-semibold uppercase tracking-wide transition-all border border-transparent hover:border-slate-700">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                    Override
                </button>
                <button onclick="window.deleteMeter('${s.meter_id}')" 
                        class="flex items-center justify-center gap-2 text-red-400/80 hover:text-red-400 hover:bg-red-500/10 px-3 py-2 rounded-xl text-xs font-semibold uppercase tracking-wide transition-all border border-transparent hover:border-red-500/20">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                    </svg>
                    Remove
                </button>
            </footer>
        </article>
    `}function pS(s){const t=(s.surplus_energy||0)>0,e=(s.deficit_energy||0)>0,a=qi(s.meter_id),i=s.battery_level||0,n={Solar_Prosumer:{bg:"bg-amber-500/20",text:"text-amber-400",label:"Solar"},Grid_Consumer:{bg:"bg-blue-500/20",text:"text-blue-400",label:"Consumer"},Hybrid_Prosumer:{bg:"bg-purple-500/20",text:"text-purple-400",label:"Hybrid"},Battery_Storage:{bg:"bg-emerald-500/20",text:"text-emerald-400",label:"Storage"}},r=n[s.meter_type]||n.Grid_Consumer,h=t?`<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400"><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>${(s.surplus_energy||0).toFixed(1)}</span>`:e?`<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-orange-500/20 text-orange-400"><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>${(s.deficit_energy||0).toFixed(1)}</span>`:'<span class="text-[10px] text-slate-500">—</span>',c=i>60?"bg-emerald-500":i>30?"bg-amber-500":"bg-red-500";return`
        <tr class="group border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors" id="row-${s.meter_id}">
            <td class="px-3 py-2">
                <div class="flex items-center gap-2">
                    <span class="h-2 w-2 rounded-full ${a?"bg-emerald-400 animate-pulse":"bg-slate-600"}"></span>
                    <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${r.bg} ${r.text}">${r.label}</span>
                </div>
            </td>
            <td class="px-3 py-2">
                <button onclick="window.openMeterDetails('${s.meter_id}')" class="text-xs font-mono text-slate-300 hover:text-white hover:underline transition-colors">${s.meter_id}</button>
            </td>
            <td class="px-3 py-2 text-right">
                <span class="text-xs font-semibold tabular-nums text-amber-400 val-gen">${(s.energy_generated||0).toFixed(1)}</span>
            </td>
            <td class="px-3 py-2 text-right">
                <span class="text-xs font-semibold tabular-nums text-blue-400 val-cons">${(s.energy_consumed||0).toFixed(1)}</span>
            </td>
            <td class="px-3 py-2">
                <div class="flex items-center gap-1.5">
                <div class="flex items-center gap-2">
                    <div class="w-16 h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div class="h-full rounded-full ${c} val-batt-bar transition-all duration-300" style="width: ${Math.max(i,3)}%"></div>
                    </div>
                    <span class="text-xs font-medium tabular-nums text-slate-400 val-batt-text w-9 text-right">${i.toFixed(0)}%</span>
                </div>
                </div>
            </td>
            <td class="px-3 py-2 text-center">${h}</td>
            <td class="px-3 py-2 text-right">
                <button onclick="window.openMeterDetails('${s.meter_id}')" class="p-1 text-slate-500 hover:text-white hover:bg-slate-700 rounded transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
                </button>
            </td>
        </tr>
    `}function gS(s,t){const e=s.querySelector(".val-gen");e&&(e.textContent=(t.energy_generated||0).toFixed(2));const a=s.querySelector(".val-cons");a&&(a.textContent=(t.energy_consumed||0).toFixed(2));const i=s.querySelector(".val-batt-text");i&&(i.textContent=`${(t.battery_level||0).toFixed(1)}%`);const n=s.querySelector(".val-batt-bar");n&&(n.style.width=`${Math.max(t.battery_level||0,2)}%`);const r=s.querySelector(".val-temp");r&&(r.textContent=`${(t.temperature||0).toFixed(1)}°C`);const h=s.querySelector(".val-emission");h&&(h.textContent=`${(t.net_emission||0).toFixed(3)} kg`);const c=s.querySelector(".status-container");if(c){c.innerHTML="";const l=(t.surplus_energy||0)>0,d=(t.deficit_energy||0)>0;l?c.innerHTML=`
                <div class="group/status flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/15 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 group-hover/status:scale-110 transition-transform">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>
                            </svg>
                        </div>
                        <div>
                            <span class="block text-[10px] font-bold text-emerald-400 uppercase tracking-wider leading-none mb-1">Selling</span>
                            <span class="text-xs text-slate-300 font-medium">${(t.surplus_energy||0).toFixed(2)} kWh</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="block text-[10px] font-medium text-emerald-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                        <span class="text-base font-bold text-emerald-400">$${(t.max_sell_price||0).toFixed(2)}</span>
                    </div>
                </div>
            `:d?c.innerHTML=`
                <div class="group/status flex items-center justify-between p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/15 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400 group-hover/status:scale-110 transition-transform">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>
                            </svg>
                        </div>
                        <div>
                            <span class="block text-[10px] font-bold text-amber-400 uppercase tracking-wider leading-none mb-1">Buying</span>
                            <span class="text-xs text-slate-300 font-medium">${(t.deficit_energy||0).toFixed(2)} kWh</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="block text-[10px] font-medium text-amber-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                        <span class="text-base font-bold text-amber-400">$${(t.max_buy_price||0).toFixed(2)}</span>
                    </div>
                </div>
            `:c.innerHTML=`
                 <div class="flex items-center justify-center gap-2 py-3 px-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500">
                        <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                    </svg>
                    <span class="text-xs text-slate-500 font-medium">System Balanced</span>
                </div>
            `}}function Yi(s,t=""){const e=document.getElementById(`${t}auto-${s}`),a=document.getElementById(`${t}manual-${s}`),i=document.getElementById(`${t}mode-btn-${s}`);a.classList.contains("hidden")?(e.classList.add("hidden"),a.classList.remove("hidden"),i.innerHTML=`
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
            </svg>
            AUTO
        `,i.classList.remove("text-primary","hover:bg-primary/10"),i.classList.add("text-accent","hover:bg-accent/10")):(a.classList.add("hidden"),e.classList.remove("hidden"),i.innerHTML=`
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/>
            </svg>
            MANUAL
        `,i.classList.remove("text-accent","hover:bg-accent/10"),i.classList.add("text-primary","hover:bg-primary/10"))}function uS(){document.getElementById("add-meter-modal").classList.remove("hidden"),document.getElementById("add-meter-form").reset(),fS()}function Ki(s){(!s||s.target.id==="add-meter-modal"||s.type==="click")&&document.getElementById("add-meter-modal").classList.add("hidden")}function fS(){const s=document.getElementById("meter-type").value,t=document.getElementById("solar-capacity-field"),e=document.getElementById("battery-capacity-field");s==="Solar_Prosumer"||s==="Hybrid_Prosumer"?t.style.display="block":t.style.display="none",s==="Hybrid_Prosumer"||s==="Battery_Storage"?e.style.display="block":e.style.display="none"}function Ji(s){(!s||s.target.id==="meter-details-modal"||s.type==="click")&&document.getElementById("meter-details-modal").classList.add("hidden")}function vS(s){const t=q.find(n=>n.meter_id===s);if(!t)return;const e=document.getElementById("meter-details-modal"),a=document.getElementById("meter-details-content"),i=xS(t);a.innerHTML=i,e.classList.remove("hidden")}function xS(s){const t=(s.surplus_energy||0)>0,e=(s.deficit_energy||0)>0;return`
        <article class="w-full rounded-[2rem] border border-white/10 bg-slate-900/90 backdrop-blur-xl shadow-2xl p-8 space-y-8 relative overflow-hidden">
             <!-- Background Decorative Gradients -->
            <div class="absolute -top-24 -right-24 w-64 h-64 bg-primary/20 rounded-full blur-[100px] pointer-events-none"></div>
            <div class="absolute -bottom-24 -left-24 w-64 h-64 bg-purple-500/20 rounded-full blur-[100px] pointer-events-none"></div>

            <!-- Header -->
            <header class="relative flex items-start justify-between gap-6 pb-6 border-b border-white/5">
                <div class="space-y-1.5 flex-1 min-w-0">
                    <div class="flex items-center gap-3">
                        <div class="p-2 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/5 shadow-inner shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
                                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>
                            </svg>
                        </div>
                        <h2 class="text-3xl font-bold text-white tracking-tight truncate" title="${s.location}">${s.location}</h2>
                    </div>
                    <p class="font-mono text-sm text-slate-400 pl-[3.25rem] truncate">${s.meter_id}</p>
                </div>
                
                <div class="flex flex-col items-end gap-2 shrink-0">
                     <div class="flex items-center gap-3">
                        <span class="inline-flex items-center gap-2 rounded-full pl-2 pr-3 py-1 text-xs font-bold tracking-wider uppercase border ${s.is_connected?"bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]":"bg-rose-500/10 text-rose-400 border-rose-500/20"}">
                            <span class="relative flex h-2.5 w-2.5">
                            <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${s.is_connected?"bg-emerald-400":"bg-rose-400"}"></span>
                            <span class="relative inline-flex rounded-full h-2.5 w-2.5 ${s.is_connected?"bg-emerald-500":"bg-rose-500"}"></span>
                            </span>
                            ${s.is_connected?"Online":"Offline"}
                        </span>
                        <button onclick="closeMeterDetails()" class="p-1 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-white/5">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M18 6 6 18"/><path d="M6 6 18 18"/>
                            </svg>
                        </button>
                    </div>
                     <div class="px-2.5 py-0.5 rounded-lg bg-slate-800/50 border border-white/5 text-[10px] font-medium text-slate-400 self-end mr-[36px]">
                        v1.0.2
                    </div>
                </div>
            </header>

            <div class="relative grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Left Column: Primary Stats -->
                <div class="space-y-6">
                    <div class="flex items-center justify-between">
                         <h3 class="text-base font-semibold text-slate-200 flex items-center gap-2">
                            <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                            Power Flow
                        </h3>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                         <!-- Generation Card -->
                         <article class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-white/5 p-5 transition-all duration-300 hover:scale-[1.02] hover:border-amber-400/30 hover:shadow-[0_0_30px_rgba(251,191,36,0.1)]">
                            <div class="absolute inset-0 bg-amber-400/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            <div class="relative z-10">
                                <div class="flex items-center gap-2 mb-4">
                                    <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-400/10 text-amber-400 group-hover:bg-amber-400 group-hover:text-black transition-colors duration-300">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>
                                        </svg>
                                    </div>
                                    <span class="text-xs font-bold text-amber-400/80 uppercase tracking-widest">Gen</span>
                                </div>
                                <div class="space-y-1">
                                    <div class="text-3xl font-bold tracking-tight text-white tabular-nums group-hover:text-amber-400 transition-colors">${(s.energy_generated||0).toFixed(2)}</div>
                                    <div class="text-xs font-medium text-slate-500">kWh produced</div>
                                </div>
                            </div>
                        </article>

                        <!-- Consumption Card -->
                        <article class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-white/5 p-5 transition-all duration-300 hover:scale-[1.02] hover:border-cyan-400/30 hover:shadow-[0_0_30px_rgba(34,211,238,0.1)]">
                            <div class="absolute inset-0 bg-cyan-400/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                             <div class="relative z-10">
                                <div class="flex items-center gap-2 mb-4">
                                    <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400 group-hover:bg-cyan-400 group-hover:text-black transition-colors duration-300">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
                                        </svg>
                                    </div>
                                    <span class="text-xs font-bold text-cyan-400/80 uppercase tracking-widest">Cons</span>
                                </div>
                                <div class="space-y-1">
                                    <div class="text-3xl font-bold tracking-tight text-white tabular-nums group-hover:text-cyan-400 transition-colors">${(s.energy_consumed||0).toFixed(2)}</div>
                                    <div class="text-xs font-medium text-slate-500">kWh used</div>
                                </div>
                            </div>
                        </article>
                    </div>

                    <!-- Battery Section -->
                    <section class="group relative rounded-2xl bg-slate-900/50 border border-white/5 p-5 transition-all hover:bg-slate-900/80">
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center gap-3">
                                <div class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/>
                                    </svg>
                                </div>
                                <div>
                                    <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">Storage</span>
                                    <span class="text-lg font-bold tabular-nums text-white">${(s.battery_level||0).toFixed(1)}%</span>
                                </div>
                            </div>
                             <div class="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">Optimal</div>
                        </div>
                        <div class="relative h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                            <div class="absolute top-0 left-0 h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-all duration-1000 ease-out" 
                                 style="width: ${s.battery_level||0}%">
                            </div>
                        </div>
                    </section>

                     <!-- Status Banners -->
                    <div class="space-y-3">
                        ${t?`
                            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20 p-4">
                                <div class="flex items-center justify-between relative z-10">
                                    <div class="flex items-center gap-3">
                                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500 text-black shadow-lg shadow-emerald-500/20">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <span class="block text-sm font-bold text-emerald-400">Exporting</span>
                                            <span class="text-xs text-emerald-400/70">Selling surplus to grid</span>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-xl font-bold tabular-nums text-white">${(s.surplus_energy||0).toFixed(2)}</div>
                                        <div class="text-xs font-medium text-emerald-400/70">kWh</div>
                                    </div>
                                </div>
                            </div>
                        `:""}
                        ${e?`
                            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-rose-500/10 to-rose-500/5 border border-rose-500/20 p-4">
                                <div class="flex items-center justify-between relative z-10">
                                    <div class="flex items-center gap-3">
                                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500 text-white shadow-lg shadow-rose-500/20">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <span class="block text-sm font-bold text-rose-400">Importing</span>
                                            <span class="text-xs text-rose-400/70">Buying from grid</span>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-xl font-bold tabular-nums text-white">${(s.deficit_energy||0).toFixed(2)}</div>
                                        <div class="text-xs font-medium text-rose-400/70">kWh</div>
                                    </div>
                                </div>
                            </div>
                        `:""}
                        ${!t&&!e?`
                            <div class="flex items-center justify-center gap-2 p-4 rounded-2xl border border-dashed border-slate-700 bg-slate-800/30">
                                <span class="h-2 w-2 rounded-full bg-slate-500"></span>
                                <span class="text-sm font-medium text-slate-400">Grid Balanced</span>
                            </div>
                        `:""}
                    </div>
                </div>

                <!-- Right Column: Technical Specs & Controls -->
                <div class="space-y-6">
                    <div class="flex items-center justify-between">
                         <h3 class="text-base font-semibold text-slate-200 flex items-center gap-2">
                            <svg class="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                            Metrics
                        </h3>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-3">
                         <!-- Metric Item -->
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Voltage</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(s.voltage||240).toFixed(1)}</span>
                                <span class="text-xs text-slate-500">V</span>
                            </div>
                        </div>
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Current</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(s.current||0).toFixed(3)}</span>
                                <span class="text-xs text-slate-500">A</span>
                            </div>
                        </div>
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Frequency</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(s.frequency||50).toFixed(2)}</span>
                                <span class="text-xs text-slate-500">Hz</span>
                            </div>
                        </div>
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Temp</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(s.temperature||0).toFixed(1)}</span>
                                <span class="text-xs text-slate-500">°C</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Identity & Pricing Compact Info -->
                    <div class="grid grid-cols-2 gap-4 pt-2">
                        <div class="space-y-2">
                             <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider">Identity</h4>
                             <div class="px-3 py-2 bg-slate-800/50 rounded-lg border border-white/5 text-xs text-slate-300 font-mono truncate">
                                Zone ${s.grid_zone_id||0}
                             </div>
                        </div>
                         <div class="space-y-2">
                             <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider">Market</h4>
                             <div class="flex gap-2">
                                <div class="px-2 py-1 bg-emerald-500/10 rounded border border-emerald-500/20 text-xs font-bold text-emerald-400">S: $${(s.max_sell_price||0).toFixed(2)}</div>
                                <div class="px-2 py-1 bg-rose-500/10 rounded border border-rose-500/20 text-xs font-bold text-rose-400">B: $${(s.max_buy_price||0).toFixed(2)}</div>
                             </div>
                        </div>
                    </div>

                    <!-- P2P Simulation Section -->
                    <div class="pt-4 border-t border-white/5">
                        <div class="p-5 bg-gradient-to-br from-purple-500/5 to-blue-500/5 rounded-2xl border border-purple-500/10">
                            <h3 class="text-sm font-bold text-purple-300 mb-4 flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                P2P Trace Simulation
                            </h3>
                            
                            <div class="flex gap-3 mb-3">
                                <div class="w-1/3">
                                    <label class="text-[10px] font-bold text-purple-300/70 uppercase tracking-wider block mb-1.5 pl-1">Target Zone</label>
                                    <input type="number" id="p2p-target-zone-${s.meter_id}" min="0" max="4" value="${s.grid_zone_id===0?1:0}"
                                           class="w-full px-3 py-2 bg-slate-900/80 border border-purple-500/20 rounded-xl text-white text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition-all placeholder-slate-600">
                                </div>
                                <div class="w-2/3">
                                   <label class="text-[10px] font-bold text-purple-300/70 uppercase tracking-wider block mb-1.5 pl-1">Energy Amount</label>
                                    <input type="number" id="p2p-amount-${s.meter_id}" min="1" value="10"
                                           class="w-full px-3 py-2 bg-slate-900/80 border border-purple-500/20 rounded-xl text-white text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition-all placeholder-slate-600">
                                </div>
                            </div>
                            
                            <button onclick="window.runP2PCheck('${s.meter_id}', ${s.grid_zone_id||0})" 
                                    class="w-full py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-xs font-bold uppercase tracking-wider rounded-xl shadow-lg shadow-purple-900/20 transition-all hover:shadow-purple-900/40 active:scale-[0.98]">
                                    Run Simulation
                            </button>
                            <div id="p2p-result-${s.meter_id}" class="hidden mt-3 p-3 bg-slate-900/80 rounded-xl text-xs border border-purple-500/20"></div>
                        </div>
                    </div>

                    <!-- Manual Controls Accordion-like -->
                    <div class="pt-4 border-t border-white/5">
                        <details class="group">
                            <summary class="flex items-center justify-between cursor-pointer list-none text-slate-400 hover:text-white transition-colors">
                                <h3 class="text-sm font-semibold">Manual Overrides</h3>
                                <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                            </summary>
                            
                            <div class="pt-4 animate-in slide-in-from-top-2 duration-200">
                                <div class="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5 pl-1">Gen (kWh)</label>
                                        <input type="number" id="modal-gen-${s.meter_id}" step="0.01" min="0" 
                                               value="${(s.energy_generated||0).toFixed(2)}"
                                               class="w-full px-3 py-2 bg-slate-800/50 border border-white/10 rounded-xl text-white text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                                    </div>
                                    <div>
                                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5 pl-1">Cons (kWh)</label>
                                        <input type="number" id="modal-cons-${s.meter_id}" step="0.01" min="0" 
                                               value="${(s.energy_consumed||0).toFixed(2)}"
                                               class="w-full px-3 py-2 bg-slate-800/50 border border-white/10 rounded-xl text-white text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                                    </div>
                                </div>
                                <div class="flex gap-3">
                                    <button onclick="window.applyManualValues('${s.meter_id}', 'modal-')" 
                                            class="flex-1 py-2 bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                                        Apply
                                    </button>
                                    <button onclick="window.resetToAuto('${s.meter_id}', 'modal-')" 
                                            class="flex-1 py-2 bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 border border-white/5 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                                        Reset
                                    </button>
                                </div>
                                
                                <!-- Hidden inputs -->
                                <input type="hidden" id="modal-batt-${s.meter_id}" value="${(s.battery_level||0).toFixed(0)}">
                                <input type="hidden" id="modal-temp-${s.meter_id}" value="${(s.temperature||25).toFixed(1)}">
                                <input type="hidden" id="modal-volt-${s.meter_id}" value="${(s.voltage||240).toFixed(1)}">
                                <input type="hidden" id="modal-curr-${s.meter_id}" value="${(s.current||0).toFixed(3)}">
                                <input type="hidden" id="modal-freq-${s.meter_id}" value="${(s.frequency||50).toFixed(2)}">
                                <input type="hidden" id="modal-sell-${s.meter_id}" value="${(s.max_sell_price||.12).toFixed(2)}">
                                <input type="hidden" id="modal-buy-${s.meter_id}" value="${(s.max_buy_price||.28).toFixed(2)}">
                            </div>
                        </details>
                    </div>
                </div>
            </div>

            <!-- Footer Actions -->
            <footer class="flex items-center justify-between pt-6 border-t border-white/5">
                <div class="text-[10px] text-slate-600">
                    ID: ${s.meter_id}
                </div>
                <button onclick="window.deleteMeter('${s.meter_id}')" 
                        class="group inline-flex items-center gap-2 text-rose-500/70 hover:text-rose-400 hover:bg-rose-500/10 px-4 py-2 rounded-xl transition-all">
                    <svg class="opacity-50 group-hover:opacity-100 transition-opacity" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>
                    </svg>
                    <span class="text-xs font-bold tracking-wider">DELETE UNIT</span>
                </button>
            </footer>
        </article>
    `}let qt=0,ee=!0;function A(s,t="info"){const e=new Date().toLocaleTimeString(),a=document.getElementById("console-output");let i="";switch(t){case"error":i="console-error";break;case"warning":i="console-warning";break;case"status":i="console-status";break;default:i="text-green-400";break}const n=document.createElement("div");if(n.className=i,n.innerHTML=`<span class="console-timestamp">[${e}]</span> ${s}`,a.appendChild(n),qt++,ee&&(a.scrollTop=a.scrollHeight),qt>1e3){const r=a.firstChild;r&&(a.removeChild(r),qt--)}}function mS(s){const t=new Date().toLocaleTimeString(),e=document.getElementById("console-output"),a=document.createElement("div");let i=`<span class="console-timestamp">[${t}]</span> `;if(i+=`<span class="console-meter-id">${s.meter_id||"UNKNOWN"}</span> `,i+=`| <span class="text-gray-400">${s.meter_type||"Unknown"}</span> `,s.energy_generated&&parseFloat(s.energy_generated)>0&&(i+=`| <span class="console-energy">Generated: ${parseFloat(s.energy_generated).toFixed(2)} kWh</span> `),s.energy_consumed&&parseFloat(s.energy_consumed)>0&&(i+=`| <span class="console-energy">Consumed: ${parseFloat(s.energy_consumed).toFixed(2)} kWh</span> `),s.surplus_energy&&parseFloat(s.surplus_energy)>0&&(i+=`| <span class="console-status">SELL: ${parseFloat(s.surplus_energy).toFixed(2)} kWh</span> `,s.max_sell_price&&(i+=`@ <span class="console-price">$${parseFloat(s.max_sell_price).toFixed(2)}</span>`)),s.deficit_energy&&parseFloat(s.deficit_energy)>0&&(i+=`| <span class="console-warning">BUY: ${parseFloat(s.deficit_energy).toFixed(2)} kWh</span> `,s.max_buy_price&&(i+=`@ <span class="console-price">$${parseFloat(s.max_buy_price).toFixed(2)}</span>`)),s.battery_level!==void 0&&(i+=`| Battery: ${parseFloat(s.battery_level).toFixed(1)}%`),s.location&&(i+=` | Location: ${s.location}`),a.innerHTML=i,e.appendChild(a),qt++,ee&&(e.scrollTop=e.scrollHeight),qt>1e3){const n=e.firstChild;n&&(e.removeChild(n),qt--)}}function MS(){const s=document.getElementById("console-output");s.innerHTML='<div class="text-gray-500">Console cleared</div>',qt=1,A("Console cleared by user","status")}function yS(){ee=!ee;const s=document.getElementById("console-scroll-btn");ee?(s.className="text-[10px] font-bold text-emerald-400 hover:text-emerald-300 uppercase tracking-wider transition-colors flex items-center gap-1.5",s.innerHTML='<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Auto-scroll'):(s.className="text-[10px] font-bold text-slate-500 hover:text-slate-400 uppercase tracking-wider transition-colors flex items-center gap-1.5",s.innerHTML='<span class="w-1.5 h-1.5 rounded-full bg-slate-600"></span> Auto-scroll'),A(`Auto-scroll ${ee?"enabled":"disabled"}`,"status")}function bS(s){s.forEach(h=>{nS(h)});let t=0,e=0,a=0,i=0;q.forEach(h=>{const c=parseFloat(h.energy_generated||0),l=parseFloat(h.energy_consumed||0);t+=c,e+=l,a+=parseFloat(h.surplus_energy||0),((h.surplus_energy||0)>0||(h.deficit_energy||0)>0)&&i++}),a1("total-generation",parseFloat(document.getElementById("total-generation").textContent),t),a1("total-consumption",parseFloat(document.getElementById("total-consumption").textContent),e),a1("total-surplus",parseFloat(document.getElementById("total-surplus").textContent),a),a1("active-traders",parseInt(document.getElementById("active-traders").textContent),i),i1("gen-trend","gen-change",t,_e.gen),i1("cons-trend","cons-change",e,_e.cons),i1("surplus-trend","surplus-change",a,_e.surplus),i1("traders-trend","traders-change",i,_e.traders,!1),rS({gen:t,cons:e,surplus:a,traders:i});let n=0,r=0;if(s.length>0){const h=s[0];n=parseFloat(h.max_sell_price||0),r=parseFloat(h.max_buy_price||0)}sS({total_generation:t,total_consumption:e,market_prices:{sell:n,buy:r}}),s.length>0&&(document.getElementById("current-weather").textContent=s[0].weather_condition||"-"),document.getElementById("total-count").textContent=q.length,Ze()}function a1(s,t,e){const a=document.getElementById(s),i=500,n=performance.now();function r(h){const c=h-n,l=Math.min(c/i,1),d=t+(e-t)*l;a.textContent=s==="active-traders"?Math.round(d):d.toFixed(2),l<1?requestAnimationFrame(r):a.textContent=s==="active-traders"?Math.round(e):e.toFixed(2)}requestAnimationFrame(r)}function i1(s,t,e,a,i=!0){const n=document.getElementById(s),r=document.getElementById(t),h=e-a,c=a>0?h/a*100:0;h>0?(n.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-1"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>${Math.abs(c).toFixed(1)}%`,n.className="text-xs font-semibold px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20 flex items-center",r.textContent=`+${i?h.toFixed(2):h}`,r.className="text-xs text-emerald-400 font-semibold"):h<0?(n.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-1"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>${Math.abs(c).toFixed(1)}%`,n.className="text-xs font-semibold px-2 py-1 bg-red-500/10 text-red-400 rounded-full border border-red-500/20 flex items-center",r.textContent=`${i?h.toFixed(2):h}`,r.className="text-xs text-red-400 font-semibold"):(n.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-1"><path d="M5 12h14"/></svg>0%',n.className="text-xs font-semibold px-2 py-1 bg-slate-700/50 text-slate-400 rounded-full border border-slate-600/50 flex items-center",r.textContent=i?"0.00":"0",r.className="text-xs text-slate-500 font-semibold")}function Ze(){const s=document.getElementById("meter-search").value.toLowerCase(),t=document.getElementById("meter-type-filter").value,e=document.getElementById("meter-status-filter").value,a=document.getElementById("readings-container"),i=cS(),n=ks(),r=Xi(),h=q.filter(x=>{const m=!s||x.meter_id.toLowerCase().includes(s)||x.location&&x.location.toLowerCase().includes(s),M=!t||x.meter_type===t;let b=!0;return e==="selling"?b=(x.surplus_energy||0)>0:e==="buying"?b=(x.deficit_energy||0)>0:e==="idle"&&(b=(x.surplus_energy||0)===0&&(x.deficit_energy||0)===0),m&&M&&b}),c=h.length,l=Math.ceil(c/r),d=(n-1)*r,p=d+r,g=h.slice(d,p);document.getElementById("filtered-count").textContent=c;const u=document.getElementById("pagination-info");u&&(u.innerHTML=`Page ${n} of ${l||1} (${d+1}-${Math.min(p,c)} of ${c})`);const f=document.getElementById("prev-page"),v=document.getElementById("next-page");if(f&&(f.disabled=n<=1),v&&(v.disabled=n>=l),h.length===0){a.innerHTML='<div class="col-span-full text-center text-gray-500 py-8">No meters match your filters</div>';return}if(i==="list")a.className="w-full",a.innerHTML=`
            <table class="w-full text-left">
                <thead class="border-b border-slate-700">
                    <tr class="text-[10px] uppercase tracking-wider text-slate-500">
                        <th class="px-3 py-2 font-medium">Type</th>
                        <th class="px-3 py-2 font-medium">Meter ID</th>
                        <th class="px-3 py-2 font-medium text-right">Gen</th>
                        <th class="px-3 py-2 font-medium text-right">Use</th>
                        <th class="px-3 py-2 font-medium">Battery</th>
                        <th class="px-3 py-2 font-medium text-center">Status</th>
                        <th class="px-3 py-2 font-medium text-right"></th>
                    </tr>
                </thead>
                <tbody id="meter-table-body">
                    ${g.map(x=>pS(x)).join("")}
                </tbody>
            </table>
        `;else{a.className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4",new Set(Array.from(a.children).map(m=>m.id.replace("card-","")));const x=new Set(g.map(m=>m.meter_id));Array.from(a.children).forEach(m=>{const M=m.id.replace("card-","");x.has(M)||m.remove()}),g.forEach(m=>{const M=`card-${m.meter_id}`,b=document.getElementById(M);if(b)gS(b,m);else{const w=dS(m),y=document.createElement("div");y.innerHTML=w.trim(),a.appendChild(y.firstChild)}})}}let fe=null,ve=null;function Qi(){const t=`${window.location.protocol==="https:"?"wss:":"ws:"}//${window.location.host}/ws`;console.log("Connecting to WebSocket:",t),fe=new WebSocket(t),fe.onopen=()=>{console.log("Connected to WebSocket"),j1(!0),A("WebSocket connected successfully","status"),ve&&(clearInterval(ve),ve=null)},fe.onmessage=e=>{try{const a=JSON.parse(e.data);let i=[];a.type==="meter_reading"?i=[a.reading]:a.type==="meter_readings"?i=a.readings||[]:Array.isArray(a)?i=a:i=[a],bS(i),i.forEach(n=>{mS(n)})}catch(a){console.error("Error parsing WebSocket message:",a),A(`Error parsing message: ${a.message}`,"error")}},fe.onerror=e=>{console.error("WebSocket error:",e),j1(!1),A("WebSocket connection error","error")},fe.onclose=()=>{console.log("WebSocket disconnected"),j1(!1),A("WebSocket connection lost","warning"),ve||(ve=setInterval(()=>{console.log("Attempting to reconnect..."),A("Attempting to reconnect...","warning"),Qi()},5e3))}}function j1(s){const t=document.getElementById("connection-status");s?t.innerHTML='<span class="inline-block w-3 h-3 rounded-full bg-emerald-500 mr-2"></span><span class="font-semibold text-emerald-400">Connected</span>':t.innerHTML='<span class="inline-block w-3 h-3 rounded-full bg-red-500 mr-2"></span><span class="font-semibold text-red-400">Disconnected</span>'}async function oe(){try{const s=await pt.getStatus();s.mode&&(document.getElementById("simulator-mode").textContent=s.mode),re({running:s.running,paused:s.paused,num_meters:s.num_meters})}catch(s){console.error("Error fetching status:",s)}}async function wS(){try{V("Starting simulation...","info"),A("Starting simulation...","status");const s=await pt.startSimulation();if(s.success)V("Simulation started successfully","success"),A("Simulation started successfully","status"),re(s.status);else{const t=s.detail||s.message||"Unknown error";V(`Failed to start: ${t}`,"error"),A(`Failed to start: ${t}`,"error")}}catch(s){const t=s.message||"Unknown error";V(`Error starting simulation: ${t}`,"error"),A(`Error starting simulation: ${t}`,"error")}}async function _S(){try{V("Stopping simulation...","info"),A("Stopping simulation...","status");const s=await pt.stopSimulation();if(s.success)V("Simulation stopped","success"),A("Simulation stopped","status"),re(s.status);else{const t=s.detail||s.message||"Unknown error";V(`Failed to stop: ${t}`,"error"),A(`Failed to stop: ${t}`,"error")}}catch(s){const t=s.message||"Unknown error";V(`Error stopping simulation: ${t}`,"error"),A(`Error stopping simulation: ${t}`,"error")}}async function kS(){try{V("Pausing simulation...","info"),A("Pausing simulation...","status");const s=await pt.pauseSimulation();if(s.success)V("Simulation paused","success"),A("Simulation paused","status"),re(s.status);else{const t=s.detail||s.message||"Unknown error";V(`Failed to pause: ${t}`,"error"),A(`Failed to pause: ${t}`,"error")}}catch(s){const t=s.message||"Unknown error";V(`Error pausing simulation: ${t}`,"error"),A(`Error pausing simulation: ${t}`,"error")}}async function CS(){try{V("Resuming simulation...","info"),A("Resuming simulation...","status");const s=await pt.resumeSimulation();if(s.success)V("Simulation resumed","success"),A("Simulation resumed","status"),re(s.status);else{const t=s.detail||s.message||"Unknown error";V(`Failed to resume: ${t}`,"error"),A(`Failed to resume: ${t}`,"error")}}catch(s){const t=s.message||"Unknown error";V(`Error resuming simulation: ${t}`,"error"),A(`Error resuming simulation: ${t}`,"error")}}async function SS(){try{V("Restarting simulation...","info"),A("Restarting simulation...","status");const s=await pt.restartSimulation();if(s.success)V("Simulation restarted","success"),A("Simulation restarted","status"),re(s.status);else{const t=s.detail||s.message||"Unknown error";V(`Failed to restart: ${t}`,"error"),A(`Failed to restart: ${t}`,"error")}}catch(s){const t=s.message||"Unknown error";V(`Error restarting simulation: ${t}`,"error"),A(`Error restarting simulation: ${t}`,"error")}}async function LS(){const s=document.getElementById("meter-count").value;if(!s||s<1||s>1e3){V("Please enter a valid meter count (1-1000)","error"),A("Invalid meter count entered","error");return}try{V(`Updating to ${s} meters...`,"info"),A(`Updating to ${s} meters...`,"status");const t=await pt.updateMeterCount(parseInt(s));if(t.success)V(`Updated to ${s} meters. Restarting simulation...`,"success"),A(`Updated to ${s} meters. Restarting simulation...`,"status"),setTimeout(()=>{oe()},1e3);else{const e=t.detail||t.message||"Unknown error";V(`Failed to update meters: ${e}`,"error"),A(`Failed to update meters: ${e}`,"error")}}catch(t){const e=t.message||"Unknown error";V(`Error updating meter count: ${e}`,"error"),A(`Error updating meter count: ${e}`,"error")}}async function AS(s){s.preventDefault();const t=document.getElementById("meter-type").value,e=document.getElementById("meter-location").value,a=document.getElementById("meter-latitude").value,i=document.getElementById("meter-longitude").value;let n=0,r=0;t!=="Grid_Consumer"&&t!=="Battery_Storage"&&(n=parseFloat(document.getElementById("solar-capacity").value)||0),t!=="Grid_Consumer"&&t!=="Solar_Prosumer"&&(r=parseFloat(document.getElementById("battery-capacity").value)||0);const h=document.getElementById("trading-preference").value,c=document.getElementById("meter-id").value,l=document.getElementById("meter-wallet").value;try{V("Adding new meter...","info"),A(`Adding new ${t} meter at ${e}...`,"status");const d={meter_type:t,location:e,solar_capacity:n,battery_capacity:r,trading_preference:h,meter_id:c||null,wallet_address:l||null};a&&(d.latitude=parseFloat(a)),i&&(d.longitude=parseFloat(i));const p=await pt.addMeter(d);if(p.success)V(`Successfully added ${t} meter! Total meters: ${p.total_meters}`,"success"),A(`Added meter ${p.meter.meter_id} (${t}) at ${e}`,"status"),Ki(),oe();else{const g=p.detail||p.message||"Unknown error";V(`Error: ${g}`,"error"),A(`Failed to add meter: ${g}`,"error")}}catch(d){const p=d.message||"Unknown error";V(`Failed to add meter: ${p}`,"error"),A(`Error adding meter: ${p}`,"error")}}async function HS(s){console.log(`[Debug] deleteMeter proceeding for ${s}`);try{A(`Removing meter ${s}...`,"status");const t=await pt.deleteMeter(s);if(console.log("[Debug] deleteMeter response data:",t),t.success){V("Successfully removed meter!","success"),A(`Removed meter ${s}`,"status"),oS(s),Ji();const e=document.getElementById(`card-${s}`);if(e)e.style.opacity="0",setTimeout(()=>e.remove(),300);else{const a=document.querySelector(`[id$="card-${s}"]`);a&&a.remove()}Ze(),oe()}else{const e=t.detail||t.message||"Unknown error";V(`Error: ${e}`,"error"),A(`Failed to remove meter: ${e}`,"error")}}catch(t){const e=t.message||"Unknown error";V(`Error deleting meter: ${e}`,"error"),A(`Error removing meter: ${e}`,"error")}}async function VS(s,t,e){return console.log("P2P transaction endpoint not available"),V("P2P transactions are currently disabled","error"),null}async function I2(){console.log("Transactions endpoint not available")}async function PS(s,t=""){const e=parseFloat(document.getElementById(`${t}gen-${s}`).value),a=parseFloat(document.getElementById(`${t}cons-${s}`).value),i=parseFloat(document.getElementById(`${t}batt-${s}`).value),n=parseFloat(document.getElementById(`${t}volt-${s}`).value),r=parseFloat(document.getElementById(`${t}curr-${s}`).value),h=parseFloat(document.getElementById(`${t}freq-${s}`).value),c=parseFloat(document.getElementById(`${t}temp-${s}`).value),l=parseFloat(document.getElementById(`${t}sell-${s}`).value),d=parseFloat(document.getElementById(`${t}buy-${s}`).value);try{const p=await pt.setMeterOverride(s,{energy_generated:e,energy_consumed:a,battery_level:i,voltage:n,current:r,frequency:h,temperature:c,max_sell_price:l,max_buy_price:d});if(p.success){V(`Manual values applied to ${s}`,"success"),A(`Set ${s}: Gen=${e}kWh, Cons=${a}kWh, Batt=${i}%`,"status");const g=document.getElementById(`${t}card-${s}`);g&&g.classList.add("ring-2","ring-orange-400")}else{const g=p.detail||p.message||"Unknown error";V(g,"error")}}catch(p){const g=p.message||"Unknown error";V(`Error applying manual values: ${g}`,"error")}}async function DS(s,t=""){try{const e=await pt.clearMeterOverride(s);if(e.success){V(`${s} returned to auto mode`,"success"),A(`Reset ${s} to auto mode`,"status");const a=document.getElementById(`${t}card-${s}`);a&&a.classList.remove("ring-2","ring-orange-400"),Yi(s,t)}else{const a=e.detail||e.message||"Unknown error";V(a,"error")}}catch(e){console.error("Error resetting to auto:",e),V("Error resetting to auto","error")}}function tn(s){const t=q.length,e=Math.ceil(t/Xi());s>=1&&s<=e&&(Gi(s),Ze())}function FS(){tn(ks()+1)}function TS(){tn(ks()-1)}function BS(s){lS(s),Gi(1),Ze();const t=document.getElementById("view-card-btn"),e=document.getElementById("view-list-btn");t&&e&&(s==="card"?(t.classList.add("bg-slate-700","text-white"),t.classList.remove("text-slate-400"),e.classList.remove("bg-slate-700","text-white"),e.classList.add("text-slate-400")):(e.classList.add("bg-slate-700","text-white"),e.classList.remove("text-slate-400"),t.classList.remove("bg-slate-700","text-white"),t.classList.add("text-slate-400")))}function OS(s){hS(parseInt(s)),Ze()}function en(s,t,e){const a=new Blob([s],{type:e}),i=URL.createObjectURL(a),n=document.createElement("a");n.href=i,n.download=t,document.body.appendChild(n),n.click(),document.body.removeChild(n),URL.revokeObjectURL(i)}function ES(){const s=prompt("Export format: CSV or JSON?","CSV").toUpperCase();s==="CSV"?RS():s==="JSON"?zS():V("Invalid format. Please choose CSV or JSON","error")}function RS(){if(q.length===0){V("No data to export","warning");return}const s=["Meter ID","Type","Location","Generation (kWh)","Consumption (kWh)","Surplus (kWh)","Deficit (kWh)","Battery (%)","Weather","Timestamp"],t=q.map(a=>[a.meter_id,a.meter_type,a.location,(a.energy_generated||0).toFixed(2),(a.energy_consumed||0).toFixed(2),(a.surplus_energy||0).toFixed(2),(a.deficit_energy||0).toFixed(2),(a.battery_level||0).toFixed(1),a.weather_condition||"-",a.timestamp||new Date().toISOString()]),e=[s,...t].map(a=>a.join(",")).join(`
`);en(e,"meter-readings.csv","text/csv"),V(`Exported ${q.length} meter readings as CSV`,"success"),A(`Exported ${q.length} readings to CSV`,"status")}function zS(){if(q.length===0){V("No data to export","warning");return}const s=JSON.stringify({exported_at:new Date().toISOString(),total_meters:q.length,readings:q},null,2);en(s,"meter-readings.json","application/json"),V(`Exported ${q.length} meter readings as JSON`,"success"),A(`Exported ${q.length} readings to JSON`,"status")}at.register(...QC);class IS{constructor(){this.ctxDepth=document.getElementById("quantumDepthChart"),this.ctxNetwork=document.getElementById("quantumNetworkChart"),this.depthChart=null,this.networkChart=null,this.voltageChart=null,this.intervalId=null}init(){if(console.log("Initializing Quantum Dashboard..."),!this.ctxDepth){console.warn("Quantum chart elements not found. Skipping init.");return}this.initCharts(),this.startPolling()}initCharts(){this.depthChart=new at(this.ctxDepth,{type:"scatter",data:{datasets:[{label:"Bids (Buyers)",data:[],backgroundColor:"#ef4444",pointRadius:6,pointHoverRadius:8},{label:"Asks (Sellers)",data:[],backgroundColor:"#10b981",pointRadius:6,pointHoverRadius:8},{label:"Matched",data:[],backgroundColor:"#3b82f6",pointRadius:8,pointStyle:"star"}]},options:{responsive:!0,maintainAspectRatio:!1,scales:{x:{type:"linear",position:"bottom",title:{display:!0,text:"Price (THB/kWh)",color:"#94a3b8"},grid:{color:"#334155"},ticks:{color:"#94a3b8"}},y:{title:{display:!0,text:"Energy (kWh)",color:"#94a3b8"},grid:{color:"#334155"},ticks:{color:"#94a3b8"}}},plugins:{legend:{labels:{color:"#e2e8f0"}},tooltip:{callbacks:{label:e=>{const a=e.raw;return`${e.dataset.label}: ${a.amount} kWh @ ${a.x} THB (ID: ${a.id})`}}}}}}),this.ctxNetwork&&(this.networkChart=new at(this.ctxNetwork,{type:"line",data:{labels:[],datasets:[{label:"Optimization Score (Welfare)",data:[],borderColor:"#8b5cf6",backgroundColor:"rgba(139, 92, 246, 0.1)",fill:!0,tension:.4}]},options:{responsive:!0,maintainAspectRatio:!1,scales:{x:{display:!1},y:{grid:{color:"#334155"},ticks:{color:"#94a3b8"}}},plugins:{legend:{display:!1}}}}));const t=document.getElementById("quantumVoltageChart");t&&(this.voltageChart=new at(t,{type:"bar",data:{labels:[],datasets:[{label:"Voltage (p.u.)",data:[],backgroundColor:[],borderRadius:4}]},options:{responsive:!0,maintainAspectRatio:!1,scales:{y:{beginAtZero:!1,min:.9,max:1.1,grid:{color:"#334155"},ticks:{color:"#94a3b8"},title:{display:!0,text:"Per Unit (p.u.)",color:"#64748b"}},x:{grid:{display:!1},ticks:{color:"#94a3b8"}}},plugins:{legend:{display:!1},annotation:{annotations:{line1:{type:"line",yMin:.96,yMax:.96,borderColor:"rgba(239, 68, 68, 0.5)",borderWidth:1,borderDash:[5,5],label:{content:"Min Safe",enabled:!0,color:"red",position:"start"}},line2:{type:"line",yMin:1.04,yMax:1.04,borderColor:"rgba(239, 68, 68, 0.5)",borderWidth:1,borderDash:[5,5],label:{content:"Max Safe",enabled:!0,color:"red",position:"start"}}}}}}}))}startPolling(){console.log("P2P API disabled - polling stopped")}async fetchData(){}async fetchTransactions(){}updateTable(t){const e=document.getElementById("transaction-table-body");if(e){if(t.length===0){e.innerHTML='<tr><td colspan="7" class="px-6 py-4 text-center text-slate-500 italic">No transactions recorded yet.</td></tr>';return}e.innerHTML=t.map(a=>`
            <tr class="hover:bg-slate-700/20 transition-colors">
                <td class="px-6 py-4 text-slate-300">${new Date(a.timestamp).toLocaleString()}</td>
                <td class="px-6 py-4 font-mono text-xs text-blue-300">${a.buyer_id}</td>
                <td class="px-6 py-4 font-mono text-xs text-orange-300">${a.seller_id}</td>
                <td class="px-6 py-4 text-right font-mono text-white">${a.amount_kwh.toFixed(2)}</td>
                <td class="px-6 py-4 text-right font-mono text-emerald-400">${a.price_per_kwh.toFixed(2)}</td>
                <td class="px-6 py-4 text-right font-mono text-emerald-300 font-bold">${a.total_cost.toFixed(2)}</td>
                <td class="px-6 py-4 text-center">
                    <span class="px-2 py-0.5 rounded text-xs font-medium border ${a.transaction_type==="QUANTUM"?"bg-violet-500/10 text-violet-400 border-violet-500/30":"bg-slate-700 text-slate-300 border-slate-600"}">${a.transaction_type}</span>
                </td>
                <td class="px-6 py-4 font-mono text-xs text-slate-500" title="${a.tx_hash||""}">
                    ${a.tx_hash?a.tx_hash.substring(0,8)+"...":"-"}
                </td>
            </tr>
        `).join("")}}updateCharts(t){if(!t.matches||!this.depthChart)return;const e=t.matches.map(n=>({x:n.price_per_kwh,y:n.amount_kwh,amount:n.amount_kwh,id:`${n.buyer_id}-${n.seller_id}`})),a=t.matches.map(n=>({x:n.price_per_kwh,y:n.amount_kwh,amount:n.amount_kwh,id:n.buyer_id})),i=t.matches.map(n=>({x:n.price_per_kwh,y:n.amount_kwh,amount:n.amount_kwh,id:n.seller_id}));if(this.depthChart.data.datasets[0].data=a,this.depthChart.data.datasets[1].data=i,this.depthChart.data.datasets[2].data=e,this.depthChart.data.datasets[0].backgroundColor="#10b981",this.depthChart.data.datasets[1].backgroundColor="#ef4444",this.depthChart.update(),this.networkChart&&t.meta&&t.meta.score!==void 0){const n=t.meta.score||0,r=new Date().toLocaleTimeString();this.networkChart.data.labels.push(r),this.networkChart.data.datasets[0].data.push(n),this.networkChart.data.labels.length>20&&(this.networkChart.data.labels.shift(),this.networkChart.data.datasets[0].data.shift()),this.networkChart.update()}if(this.networkChart.update(),this.voltageChart&&t.meta&&t.meta.zone_voltages){const n=t.meta.zone_voltages,r=Object.keys(n).sort((d,p)=>parseInt(d)-parseInt(p)),h=r.map(d=>n[d]),c=h.map(d=>d>=.96&&d<=1.04?"#10b981":"#f59e0b");this.voltageChart.data.labels=r.map(d=>`Zone ${d}`),this.voltageChart.data.datasets[0].data=h,this.voltageChart.data.datasets[0].backgroundColor=c,this.voltageChart.update();const l=document.getElementById("voltage-status");if(l){const d=h.filter(p=>p<.96||p>1.04).length;d>0?(l.innerText=`${d} Zone(s) Unstable`,l.className="absolute top-2 right-2 text-xs bg-red-900/80 px-2 py-1 rounded text-red-200 border border-red-700 font-bold animate-pulse"):(l.innerText="Grid Healthy",l.className="absolute top-2 right-2 text-xs bg-emerald-900/80 px-2 py-1 rounded text-emerald-200 border border-emerald-700")}}}updateStats(t){const e=document.getElementById("quantum-duration"),a=document.getElementById("quantum-match-count"),i=document.getElementById("quantum-welfare"),n=document.getElementById("quantum-method");t.meta&&(e&&(e.innerText=(t.meta.duration||0).toFixed(3)+"s"),n&&(n.innerText=t.meta.method||"Unknown"),a&&(a.innerText=t.matches.length),i&&(i.innerText=(t.meta.score||0).toFixed(2)))}}window.toggleDarkMode=aS;window.startSimulation=wS;window.stopSimulation=_S;window.pauseSimulation=kS;window.resumeSimulation=CS;window.restartSimulation=SS;window.updateMeterCount=LS;window.openAddMeterModal=uS;window.closeAddMeterModal=Ki;window.submitAddMeter=AS;window.closeMeterDetails=Ji;window.openMeterDetails=vS;window.toggleManualMode=Yi;window.applyManualValues=PS;window.resetToAuto=DS;window.deleteMeter=HS;window.clearConsole=MS;window.toggleConsoleScroll=yS;window.exportData=ES;window.nextPage=FS;window.prevPage=TS;window.changeViewMode=BS;window.changeItemsPerPage=OS;window.runP2PCheck=async(s,t)=>{const e=document.getElementById(`p2p-target-zone-${s}`).value,a=document.getElementById(`p2p-amount-${s}`).value,i=document.getElementById(`p2p-result-${s}`);i.innerHTML="<span>Analyzing Grid Physics...</span>",i.className="mt-3 p-3 rounded-xl text-sm bg-secondary/50 text-muted-foreground",i.classList.remove("hidden");try{const n=await VS(e,t,a);n.is_grid_compliant?(i.className="mt-3 p-3 rounded-xl text-sm bg-emerald-500/10 border border-emerald-500/20 text-emerald-400",i.innerHTML=`
                <div class="flex items-center gap-2 mb-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    <span class="font-bold">Grid Compliant</span>
                </div>
                <div class="flex justify-between text-xs mt-2">
                   <span>Energy Cost:</span>
                   <span class="font-mono text-foreground">${n.energy_cost.toFixed(2)} THB</span>
                </div>
                 <div class="flex justify-between text-xs">
                   <span>Wheeling:</span>
                   <span class="font-mono text-foreground">${n.wheeling_charge.toFixed(2)} THB</span>
                </div>
                <div class="flex justify-between font-bold border-t border-emerald-500/20 pt-1 mt-1">
                   <span>Total:</span>
                   <span>${n.total_cost.toFixed(2)} THB</span>
                </div>
            `):(i.className="mt-3 p-3 rounded-xl text-sm bg-red-500/10 border border-red-500/20 text-red-500",i.innerHTML=`
                <div class="flex items-center gap-2 mb-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/></svg>
                    <span class="font-bold">Trade Rejected</span>
                </div>
                <p class="text-xs text-red-400 mt-1">${n.grid_violation_reason||"Grid Instability Detected"}</p>
                 <p class="text-xs text-red-400/70 italic mt-1">Physics Validation Failed</p>
            `)}catch(n){console.error(n),i.className="mt-3 p-3 rounded-xl text-sm bg-red-500/10 border border-red-500/20 text-red-500",i.textContent="Validation Error. See Console."}};function $2(){try{iS(),X9(),tS(),eS(),new IS().init(),Qi(),oe(),I2(),A("Smart Meter Simulator Dashboard initialized","status"),A("Waiting for real-time meter data...","info"),setInterval(()=>{oe(),I2()},5e3),console.log("Dashboard initialized successfully")}catch(s){console.error("Failed to initialize dashboard:",s),A(`Initialization error: ${s.message}`,"error")}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",$2):$2();document.addEventListener("visibilitychange",()=>{document.hidden?console.log("Page hidden - consider pausing updates"):(console.log("Page visible - resuming updates"),oe())});window.addEventListener("error",s=>{var t;console.error("Global error:",s.error),A(`Error: ${((t=s.error)==null?void 0:t.message)||"Unknown error"}`,"error")});window.addEventListener("unhandledrejection",s=>{var t;console.error("Unhandled promise rejection:",s.reason),A(`Promise rejection: ${((t=s.reason)==null?void 0:t.message)||"Unknown error"}`,"error")});
//# sourceMappingURL=main.js.map
