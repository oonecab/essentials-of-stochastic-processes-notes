
(() => {
  const lab = document.getElementById('action-lab');
  if (!lab) return;
  let state = ['A', 'B', 'C'], history = [];
  const canonical = {ABC:'e', BAC:'a', ACB:'b', BCA:'ab', CAB:'ba', CBA:'aba'};
  const move = action => {const i=action==='a'?0:1; [state[i],state[i+1]]=[state[i+1],state[i]];};
  const show = () => {
    lab.querySelectorAll('.picture').forEach((node,i) => node.textContent=state[i]);
    document.getElementById('action-word').textContent=history.join('')||'e';
    document.getElementById('action-equivalent').textContent=canonical[state.join('')];
    lab.querySelector('[data-action="undo"]').disabled=history.length===0;
  };
  lab.querySelectorAll('button').forEach(button => {
    button.disabled=false;
    button.addEventListener('click', () => {
      const action=button.dataset.action;
      if(action==='reset'){state=['A','B','C'];history=[];}
      else if(action==='undo'){if(history.length)move(history.pop());}
      else {move(action);history.push(action);}
      show();
    });
  });
  show();
})();
