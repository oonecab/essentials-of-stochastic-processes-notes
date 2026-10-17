// Browser regression: evaluate this function on each rendered chapter page.
// Chapter 9 additionally covers the six original inline-selection cases.
(() => {
  const results = [];
  function copy(name, range, expected, handled = true) {
    const selection = getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    const data = new DataTransfer();
    const event = new ClipboardEvent('copy', {bubbles: true, cancelable: true, clipboardData: data});
    document.dispatchEvent(event);
    const text = data.getData('text/plain');
    const rich = data.getData('text/html');
    if (event.defaultPrevented !== handled) throw Error(name + ' interception');
    if (expected !== null && text !== expected) throw Error(name + ' text ' + JSON.stringify(text));
    if (handled && !rich.includes('<math')) throw Error(name + ' rich MathML');
    if (document.querySelector('[style*="-100000px"]')) throw Error(name + ' temporary host retained');
    selection.removeAllRanges();
    results.push({name, handled: event.defaultPrevented, text, richMath: rich.includes('<math'), temporaryHostRemoved: true});
  }
  function visibleTexts(math) {
    const texts = [];
    const walker = document.createTreeWalker(math, NodeFilter.SHOW_TEXT, {
      acceptNode: n => n.textContent.trim() && !n.parentElement.closest('annotation')
        ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
    });
    while (walker.nextNode()) texts.push(walker.currentNode);
    return texts;
  }
  const range = document.createRange();
  const math = document.querySelector('#theorem-9-13 math[aria-label="nₚ∣|G|"]');
  if (math) {
    const paragraph = math.closest('p');
    range.selectNode(math);
    copy('whole formula', range, 'nₚ∣|G|');
    const texts = visibleTexts(math);
    range.setStart(texts[0], 0);
    range.setEnd(texts.at(-1), texts.at(-1).length);
    copy('visible formula characters', range, 'nₚ∣|G|');
    range.selectNodeContents(paragraph);
    const expected = '中文陈述：Sylow p 子群的个数 nₚ 满足 nₚ∣|G| 且 nₚ≡1 (mod p)。事实上 nₚ=[G:N_G(P)]，因 P⊆N_G(P)，还有更强的 nₚ∣m，其中 |G|=pⁿm、p∤m。';
    copy('whole paragraph', range, expected);
    const source = paragraph.nextElementSibling;
    range.setStartBefore(paragraph);
    range.setEndAfter(source);
    copy('two paragraphs', range, null);
    const last = results.at(-1);
    if (!last.text.includes(expected + '\n') || !last.text.includes('印刷 215 / PDF 230')) throw Error('paragraph break missing');
    range.setStart(texts[0], 0);
    range.setEnd(texts[0], 1);
    copy('partial formula', range, '', false);
    range.selectNodeContents(document.querySelector('#theorem-9-13 h3'));
    copy('ordinary text', range, '', false);
  }
  const displays = [...document.querySelectorAll('main math[display="block"]')];
  if (!displays.length) throw Error('display formulas missing');
  displays.forEach((display, i) => {
    const expected = display.getAttribute('aria-label');
    if (!expected || display.querySelector('annotation[encoding="text/plain"]')?.textContent !== expected) throw Error('display fallback missing');
    range.selectNode(display);
    copy('display ' + (i + 1) + ' whole', range, expected);
    const texts = visibleTexts(display);
    range.setStart(texts[0], 0);
    range.setEnd(texts.at(-1), texts.at(-1).length);
    copy('display ' + (i + 1) + ' visible', range, expected);
    range.setStart(texts[0], 0);
    range.setEnd(texts[0], 1);
    copy('display ' + (i + 1) + ' partial', range, '', false);
  });
  const equation = displays[0].closest('.equation');
  const previous = equation.previousElementSibling;
  if (!previous) throw Error('display context missing');
  range.setStartBefore(previous);
  range.setEndAfter(equation);
  copy('paragraph with display', range, null);
  const contextText = results.at(-1).text;
  const label = displays[0].getAttribute('aria-label');
  if (!contextText.includes('\n' + label)) throw Error('display paragraph boundary missing');
  if (contextText.split(label).length !== 2) throw Error('display fallback repeated');
  return results;
})
