
(() => {
  const rail = document.getElementById('annotation-rail');
  const content = document.getElementById('annotation-content');
  const context = document.getElementById('annotation-context-link');
  const groups = Array.from(document.querySelectorAll('main .reading-notes')).map(notes => ({
    notes, section: document.getElementById(notes.dataset.notesFor)
  })).filter(item => item.section);
  if (!rail || !content || !context || !groups.length) return;
  const wide = matchMedia('(min-width:1440px)');
  let current = null, scheduled = false;
  const update = () => {
    scheduled = false;
    if (!wide.matches) return;
    let next = groups[0];
    for (const item of groups) {
      if (item.section.getBoundingClientRect().top <= 110) next = item;
    }
    if (scrollY + innerHeight >= document.documentElement.scrollHeight - 2) next = groups[groups.length - 1];
    if (current === next) return;
    const body = next.notes.querySelector('.reading-notes-body');
    const heading = next.section.querySelector('h2');
    if (!body || !heading) return;
    content.replaceChildren(...Array.from(body.children, node => node.cloneNode(true)));
    context.textContent = heading.textContent;
    context.href = '#' + next.section.id;
    rail.dataset.activeSection = next.section.id;
    rail.scrollTop = 0;
    current = next;
  };
  const schedule = () => {
    if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
  };
  const fit = () => {
    rail.hidden = !wide.matches;
    current = null;
    if (wide.matches) {
      document.documentElement.classList.add('notes-enhanced');
      update();
    } else {
      document.documentElement.classList.remove('notes-enhanced');
    }
  };
  wide.addEventListener('change', fit);
  addEventListener('scroll', schedule, {passive:true});
  addEventListener('resize', schedule);
  addEventListener('hashchange', schedule);
  document.addEventListener('toggle', schedule, true);
  fit();
})();
