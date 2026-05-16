(() => {
  // ====== JA -> KO 사전 ======
  // (사전은 긴 문장부터 우선 매칭되도록 길이순 처리)
  const JA_TO_KO = {
    // 설명
    "もちふぃった～は、VRChat用の3Dアバター向けの衣装を自動で合わせるためのツールです。":
      "모치피타는 VRChat용 3D 아바타 의상을 자동으로 맞추기 위한 도구입니다.",
    "アバター向けの衣装を、もちふぃった～Templateに合わせることで、他のアバターにも着せることができます。":
      "아바타용 의상을 모치피타 템플릿에 맞추면, 다른 아바타에도 적용할 수 있습니다.",
    "順方向": "정방향",
    "Templateから別のアバターへ自動で合わせる": "템플릿 → 다른 아바타로 자동 적용",
    "逆方向": "역방향",
    "アバター用衣装をTemplateに自動で合わせる": "아바타 의상 → 템플릿으로 자동 변환",
    "新しいアバタープロファイルの登録をご希望の方は、こちらのフォームからリクエストしてください。機能追加の要望などを書いていただいても構いません。":
      "새 아바타 프로필을 등록하려면 이 양식을 사용하여 요청하십시오. 추가 기능에 대한 요청을 작성할 수 있습니다.",

    // 탭/메타
    "もちふぃった～プロファイル一覧 | VRChatアバター対応衣装・プロファイル情報":
      "모치피터 프로필 목록 | VRChat 아바타 대응 의상·프로필 정보",
    "もちふぃった～プロファイル一覧": "모치피터 프로필 목록",
    "VRChatアバター用 もちふぃった～プロファイル情報まとめ":
      "VRChat 아바타용 모치피터 프로필 정보 정리",

    // 상단/섹션
    "(WIP)軽量版ページへ": "(WIP) 경량판 페이지",
    "最終更新": "최종 업데이트",
    "読み込み中...": "불러오는 중...",
    "もちふぃった～とは？": "모치피터란?",
    "プロファイル登録要望": "프로필 등록 요청",
    "登録要望フォームを開く": "등록 요청 폼 열기",
    "購入ページは": "구매 페이지는",
    "こちら": "여기",

    // 검색/필터
    "アバター名、作者名で検索...": "아바타 이름, 제작자 이름으로 검색...",
    "アバター名、作者名で検索.": "아바타 이름, 제작자 이름으로 검색...",
    "全て": "전체",
    "公式": "공식",
    "非公式": "비공식",
    "順方向対応": "정방향 지원",
    "逆方向対応": "역방향 지원",
    "双方向対応": "양방향 지원",
    "無料": "무료",
    "単体有料": "단품 유료",
    "アバター同梱": "아바타 포함",
    "件": "건",

    // 카드
    "プロファイル一覧": "프로필 목록",
    "アバター作者": "아바타 제작자",
    "プロファイル作者": "프로필 제작자",
    "DL方法": "다운로드 방식",
    "DLリンク": "다운로드 링크",
    "備考": "비고",
    "プロファイル価格": "프로필 가격",
    "アバター価格": "아바타 가격",
    "未登録": "미등록",
    "円": "엔",
	"ダウンロード": "다운로드",
	"登録": "등록",
	"更新": "수정",

    // 지원 배지
    "順方向: 対応": "정방향: 지원",
    "順方向: 未対応": "정방향: 미지원",
    "逆方向: 対応": "역방향: 지원",
    "逆方向: 未対応": "역방향: 미지원",

    // 에러 문구
    "データの読み込みに失敗しました": "데이터를 불러오는 데 실패했습니다",
    "プロファイルデータの読み込みに失敗しました": "프로필 데이터를 불러오는 데 실패했습니다",
    "読み込み失敗": "불러오기 실패",
    "データの読み込みに失敗しました:": "데이터를 불러오는 데 실패했습니다:",
    "エラー": "오류",
	
	// 정렬
	"DB登録順（ID順）": "DB 등록순(ID순)",
	"アバター公開順（Booth ID順）": "아바타 공개순(Booth ID순)",
	"プロファイル公開順（Booth ID順）": "프로필 공개순(Booth ID순)",
	"最終更新日順（新しい順）": "최종 업데이트순(최신순)",
	"最終更新日順（古い順）": "최종 업데이트순(오래된순)",
	"アバター名順（あいうえお順）": "아바타 이름순",
	"アバター作者名順（あいうえお順）": "아바타 제작자명순",
	"プロファイル作者名順（あいうえお順）": "프로필 제작자명순",
  };

  const ATTRS = ["placeholder", "title", "aria-label"];

  // ====== 원본(일본어) 스냅샷 저장 ======
  const ORIG_TEXT = new WeakMap(); // TextNode -> original text
  const ORIG_ATTR = new WeakMap(); // Element -> { attr: original }
  let ORIG_DOC_TITLE = null;
  const ORIG_META = new Map(); // selector -> original content

  const JA_KEYS = Object.keys(JA_TO_KO).sort((a, b) => b.length - a.length);

  function escapeRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function replaceJaToKo(text) {
    if (!text) return text;
    let out = text;

    for (const k of JA_KEYS) {
      const v = JA_TO_KO[k];
      const pattern = escapeRegExp(k).replace(/\s+/g, "\\s+");
      const re = new RegExp(pattern, "g");
      out = out.replace(re, v);
    }

    return out;
  }

  function snapshotNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (!ORIG_TEXT.has(node)) ORIG_TEXT.set(node, node.nodeValue);
      return;
    }

    if (node.nodeType === Node.ELEMENT_NODE) {
      const el = node;
      if (!ORIG_ATTR.has(el)) ORIG_ATTR.set(el, {});
      const rec = ORIG_ATTR.get(el);

      for (const a of ATTRS) {
        if (el.hasAttribute && el.hasAttribute(a) && rec[a] === undefined) {
          rec[a] = el.getAttribute(a);
        }
      }
    }
  }

  function snapshotSubtree(root) {
    if (!root) return;

    snapshotNode(root);

    const walker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT
    );

    let n = walker.currentNode;
    while (n) {
      snapshotNode(n);
      n = walker.nextNode();
    }
  }

  function snapshotHead() {
    if (ORIG_DOC_TITLE === null) ORIG_DOC_TITLE = document.title;

    const metaSelectors = [
      'meta[property="og:title"]',
      'meta[property="og:description"]',
      'meta[name="twitter:title"]',
      'meta[name="twitter:description"]',
      'meta[name="description"]',
    ];

    for (const sel of metaSelectors) {
      const el = document.querySelector(sel);
      if (!el) continue;
      if (!ORIG_META.has(sel)) {
        ORIG_META.set(sel, el.getAttribute("content") || "");
      }
    }
  }

  function applyKorean(root) {
    snapshotSubtree(root);
    snapshotHead();

    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const texts = [];
    while (tw.nextNode()) texts.push(tw.currentNode);

    for (const t of texts) {
      const orig = ORIG_TEXT.get(t);
      if (orig === undefined) continue;
      const ko = replaceJaToKo(orig);
      if (t.nodeValue !== ko) t.nodeValue = ko;
    }

    const els = root.querySelectorAll ? root.querySelectorAll("*") : [];
    for (const el of els) {
      const rec = ORIG_ATTR.get(el);
      if (!rec) continue;

      for (const a of ATTRS) {
        if (rec[a] !== undefined) {
          const ko = replaceJaToKo(rec[a]);
          if (el.getAttribute(a) !== ko) el.setAttribute(a, ko);
        }
      }
    }

    if (ORIG_DOC_TITLE != null) document.title = replaceJaToKo(ORIG_DOC_TITLE);

    for (const [sel, orig] of ORIG_META.entries()) {
      const el = document.querySelector(sel);
      if (!el) continue;
      el.setAttribute("content", replaceJaToKo(orig));
    }
  }

  function restoreJapanese(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const texts = [];
    while (tw.nextNode()) texts.push(tw.currentNode);

    for (const t of texts) {
      const orig = ORIG_TEXT.get(t);
      if (orig !== undefined && t.nodeValue !== orig) t.nodeValue = orig;
    }

    const els = root.querySelectorAll ? root.querySelectorAll("*") : [];
    for (const el of els) {
      const rec = ORIG_ATTR.get(el);
      if (!rec) continue;

      for (const a of ATTRS) {
        if (rec[a] !== undefined && el.getAttribute(a) !== rec[a]) {
          el.setAttribute(a, rec[a]);
        }
      }
    }

    if (ORIG_DOC_TITLE != null) document.title = ORIG_DOC_TITLE;

    for (const [sel, orig] of ORIG_META.entries()) {
      const el = document.querySelector(sel);
      if (!el) continue;
      el.setAttribute("content", orig);
    }
  }

  function updateHtmlLang(lang) {
    document.documentElement.setAttribute("lang", lang === "ko" ? "ko" : "ja");
  }

  function getLangToggleText(lang) {
    return lang === "ko" ? "日本語で" : "한국어로";
  }

  function getLangToggleTitle(lang) {
    return lang === "ko" ? "日本語で" : "한국어로";
  }

  function updateToggleLabel(lang) {
    const btn = document.getElementById("langToggle");
    if (!btn) return;

    const text = getLangToggleText(lang);
    const title = getLangToggleTitle(lang);

    btn.textContent = text;
    btn.setAttribute("title", title);
    btn.setAttribute("aria-label", title);
  }

  // 버튼을 X 링크 왼쪽에 삽입
  function ensureToggleButton() {
    let btn = document.getElementById("langToggle");
    if (btn) return btn;

    btn = document.createElement("button");
    btn.id = "langToggle";
    btn.type = "button";

    btn.style.marginRight = "8px";
    btn.style.padding = "4px 10px";
    btn.style.borderRadius = "8px";
    btn.style.border = "1px solid rgba(255,255,255,0.25)";
    btn.style.background = "rgba(255,255,255,0.08)";
    btn.style.color = "inherit";
    btn.style.cursor = "pointer";
    btn.style.fontSize = "12px";
    btn.style.fontWeight = "600";
    btn.style.lineHeight = "1";
    btn.style.height = "36px";
    btn.style.minWidth = "72px";
    btn.style.whiteSpace = "nowrap";
    btn.style.display = "inline-flex";
    btn.style.alignItems = "center";
    btn.style.justifyContent = "center";
    btn.style.verticalAlign = "middle";
    btn.style.backdropFilter = "blur(4px)";
    btn.style.webkitBackdropFilter = "blur(4px)";
    btn.style.transition = "background-color 0.2s ease, border-color 0.2s ease, transform 0.15s ease";

    btn.addEventListener("mouseenter", () => {
      btn.style.background = "rgba(255,255,255,0.14)";
      btn.style.borderColor = "rgba(255,255,255,0.35)";
    });

    btn.addEventListener("mouseleave", () => {
      btn.style.background = "rgba(255,255,255,0.08)";
      btn.style.borderColor = "rgba(255,255,255,0.25)";
      btn.style.transform = "translateY(0)";
    });

    btn.addEventListener("mousedown", () => {
      btn.style.transform = "translateY(1px)";
    });

    btn.addEventListener("mouseup", () => {
      btn.style.transform = "translateY(0)";
    });

    const xLink = document.querySelector('a[href*="x.com"], a[href*="twitter.com"]');
    if (xLink && xLink.parentNode) {
      xLink.parentNode.insertBefore(btn, xLink);
    } else {
      document.body.prepend(btn);
    }

    btn.addEventListener("click", () => {
      const current = localStorage.getItem("lang") || "ko";
      setLang(current === "ko" ? "ja" : "ko");
    });

    return btn;
  }

  function setLang(lang) {
    snapshotSubtree(document.body);
    snapshotHead();

    if (lang === "ko") applyKorean(document.body);
    else restoreJapanese(document.body);

    localStorage.setItem("lang", lang);
    updateToggleLabel(lang);
    updateHtmlLang(lang);
  }

  // main.js가 나중에 만든 카드/라벨도 자동 번역
  function initObserver() {
    const obs = new MutationObserver((mutations) => {
      const lang = localStorage.getItem("lang") || "ko";

      for (const m of mutations) {
        for (const n of m.addedNodes) {
          if (!n) continue;
          snapshotSubtree(n);
          if (lang === "ko") applyKorean(n);
        }
      }
    });

    obs.observe(document.body, { childList: true, subtree: true });
  }

  function init() {
    ensureToggleButton();

    // 첫 방문 기본값: 한국어
    const lang = localStorage.getItem("lang") || "ko";

    snapshotSubtree(document.body);
    snapshotHead();
    setLang(lang);
    initObserver();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();