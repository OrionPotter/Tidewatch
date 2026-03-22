(function () {
  function getStack() {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    return stack;
  }

  window.showToast = function showToast(message, type = 'info', title) {
    const stack = getStack();
    const toast = document.createElement('div');
    toast.className = `toast-card ${type}`;
    const resolvedTitle = title || (type === 'success' ? '成功' : type === 'error' ? '错误' : '提示');
    toast.innerHTML = `<div class="toast-title">${resolvedTitle}</div><div class="toast-message">${message}</div>`;
    stack.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('is-visible'));

    setTimeout(() => {
      toast.classList.remove('is-visible');
      setTimeout(() => toast.remove(), 220);
    }, 2600);
  };
})();
