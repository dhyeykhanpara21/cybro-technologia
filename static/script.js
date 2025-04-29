function scrollDown() {
  window.scrollBy({
    top: window.innerHeight,
    behavior: 'smooth'
  });
}

document.addEventListener('DOMContentLoaded', function () {
  const controlsBtn = document.getElementById('controlsBtn');
  const controlsOptions = document.getElementById('controlsOptions');

  controlsBtn.addEventListener('click', function () {
    if (controlsOptions.style.display === 'flex') {
      controlsOptions.classList.remove('fade-in');
      controlsOptions.classList.add('fade-out');
      setTimeout(() => {
        controlsOptions.style.display = 'none';
      }, 500); // matches fade-out duration
    } else {
      controlsOptions.style.display = 'flex';
      controlsOptions.classList.remove('fade-out');
      controlsOptions.classList.add('fade-in');
    }
  });
});
