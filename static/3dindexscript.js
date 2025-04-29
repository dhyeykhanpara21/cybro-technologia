function scrollDown() {
    window.scrollBy({
      top: window.innerHeight,
      behavior: 'smooth'
    });
  }
  
  // Fade-in when scrolling
  const faders = document.querySelectorAll('.fade-in');
  
  const appearOptions = {
    threshold: 0.3,
  };
  
  const appearOnScroll = new IntersectionObserver(function(entries, appearOnScroll) {
    entries.forEach(entry => {
      if (!entry.isIntersecting) {
        return;
      } else {
        entry.target.classList.add('visible');
        appearOnScroll.unobserve(entry.target);
      }
    });
  }, appearOptions);
  
  faders.forEach(fader => {
    appearOnScroll.observe(fader);
  });
  