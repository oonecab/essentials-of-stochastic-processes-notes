
(() => {
  let saved=[];
  addEventListener('beforeprint',()=>{
    if(saved.length)return;
    saved=[...document.querySelectorAll('main details')].map(node=>[node,node.open]);
    saved.forEach(([node])=>{node.open=true;});
  });
  addEventListener('afterprint',()=>{
    saved.forEach(([node,open])=>{node.open=open;});saved=[];
  });
})();
