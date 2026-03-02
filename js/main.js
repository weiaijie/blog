document.addEventListener('DOMContentLoaded', function() {
  // 汉堡菜单切换
  const menuToggle = document.querySelector('.menu-toggle');
  const navList = document.querySelector('.nav-list');

  if (menuToggle && navList) {
    menuToggle.addEventListener('click', function() {
      navList.classList.toggle('active');
      document.body.classList.toggle('menu-open');
      this.setAttribute('aria-expanded',
        this.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
      );
    });

    // 点击菜单外部关闭菜单
    document.addEventListener('click', function(event) {
      if (document.body.classList.contains('menu-open') &&
          !event.target.closest('.main-nav') &&
          !event.target.closest('.menu-toggle')) {
        navList.classList.remove('active');
        document.body.classList.remove('menu-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // 滚动效果
  const header = document.querySelector('.site-header');
  let lastScrollTop = 0;
  let scrollTimer;

  function handleScroll() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    // 向下滚动超过100px时隐藏头部
    if (scrollTop > 100 && scrollTop > lastScrollTop) {
      header.classList.add('scrolled');
      header.classList.remove('visible');
    }
    // 向上滚动时显示头部
    else if (scrollTop < lastScrollTop) {
      header.classList.remove('scrolled');
      header.classList.add('visible');
    }

    lastScrollTop = scrollTop;

    // 清除之前的定时器
    clearTimeout(scrollTimer);

    // 停止滚动2秒后显示头部
    scrollTimer = setTimeout(function() {
      header.classList.remove('scrolled');
      header.classList.add('visible');
    }, 2000);
  }

  window.addEventListener('scroll', handleScroll);

  // 打字机效果
  const typewriterElement = document.getElementById('typewriter-text');
  if (typewriterElement) {
    const phrases = [
      '全栈开发工程师',
      '前端开发专家',
      '后端架构师',
      '技术爱好者',
      'UI/UX设计师'
    ];

    let currentPhraseIndex = 0;
    let currentCharIndex = 0;
    let isDeleting = false;
    let typingSpeed = 100;

    function typeEffect() {
      const currentPhrase = phrases[currentPhraseIndex];

      if (isDeleting) {
        // 删除文字
        typewriterElement.textContent = currentPhrase.substring(0, currentCharIndex - 1);
        currentCharIndex--;
        typingSpeed = 50;
      } else {
        // 添加文字
        typewriterElement.textContent = currentPhrase.substring(0, currentCharIndex + 1);
        currentCharIndex++;
        typingSpeed = 100;
      }

      // 如果完成了当前短语的输入
      if (!isDeleting && currentCharIndex === currentPhrase.length) {
        // 暂停一段时间后开始删除
        isDeleting = true;
        typingSpeed = 2000;
      } else if (isDeleting && currentCharIndex === 0) {
        // 如果删除完成，切换到下一个短语
        isDeleting = false;
        currentPhraseIndex = (currentPhraseIndex + 1) % phrases.length;
        typingSpeed = 500;
      }

      setTimeout(typeEffect, typingSpeed);
    }

    // 启动打字机效果
    setTimeout(typeEffect, 1000);
  }

  // 平滑滚动效果
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();

      const targetId = this.getAttribute('href');
      if (targetId === '#') return;

      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        const headerHeight = document.querySelector('.site-header').offsetHeight;
        window.scrollTo({
          top: targetElement.offsetTop - headerHeight - 20, // 减去头部高度和额外空间
          behavior: 'smooth'
        });

        // 如果在移动设备上，点击后关闭菜单
        if (window.innerWidth <= 768 && document.body.classList.contains('menu-open')) {
          navList.classList.remove('active');
          document.body.classList.remove('menu-open');
          menuToggle.setAttribute('aria-expanded', 'false');
        }
      }
    });
  });

  // 添加页面加载动画
  window.addEventListener('load', function() {
    document.body.classList.add('loaded');
  });
});
