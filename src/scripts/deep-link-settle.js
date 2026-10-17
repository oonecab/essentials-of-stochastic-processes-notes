(() => {
  const place = () => {
    const hash = location.hash;
    let target;
    try { target = document.getElementById(decodeURIComponent(hash.slice(1))); } catch { return; }
    if (!target || !target.closest('details')) return;
    for (let node = target; node; node = node.parentElement) {
      if (node.tagName === 'DETAILS') node.open = true;
    }
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (location.hash === hash) target.scrollIntoView({block: 'start', behavior: 'instant'});
    }));
  };
  addEventListener('hashchange', place);
  place();
})();
