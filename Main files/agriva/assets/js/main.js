(function($) {
    "use strict";
  
    const $documentOn = $(document);
    const $windowOn = $(window);
  
    $documentOn.ready( function() {
  
      /* ================================
       Mobile Menu Js Start
    ================================ */
    
      $('#mobile-menu').meanmenu({
        meanMenuContainer: '.mobile-menu',
        meanScreenWidth: "1199",
        meanExpand: ['<i class="far fa-plus"></i>'],
    });

       $('#mobile-menus').meanmenu({
        meanMenuContainer: '.mobile-menus',
        meanScreenWidth: "19920",
        meanExpand: ['<i class="far fa-plus"></i>'],
    });

     $documentOn.on("click", ".mean-expand", function () {
        let icon = $(this).find("i");

        if (icon.hasClass("fa-plus")) {
            icon.removeClass("fa-plus").addClass("fa-minus"); 
        } else {
            icon.removeClass("fa-minus").addClass("fa-plus"); 
        }
    });

    /* ================================
        Sidebar Toggle & Sticky Item Logic
        ================================ */

        // Open offcanvas
        $(".sidebar__toggle").on("click", function () {
        $(".offcanvas__info").addClass("info-open");
        $(".offcanvas__overlay").addClass("overlay-open");

        // Hide sticky item
        $(".sidebar-sticky-item").fadeOut().removeClass("active");
        });

        // Close offcanvas
        $(".offcanvas__close, .offcanvas__overlay").on("click", function () {
        $(".offcanvas__info").removeClass("info-open");
        $(".offcanvas__overlay").removeClass("overlay-open");

        // Show sticky item
        $(".sidebar-sticky-item").fadeIn().addClass("active");
        });

        /* ================================
        Body Overlay Js Start
        ================================ */

        $(".body-overlay").on("click", function () {
        $(".offcanvas__area").removeClass("offcanvas-opened");
        $(".df-search-area").removeClass("opened");
        $(".body-overlay").removeClass("opened");

        // Show sticky item when overlay clicked
        $(".sidebar-sticky-item").fadeIn().addClass("active");
        });

        /* ================================
        Offcanvas Link Click (Optional)
        ================================ */

        $(".offcanvas a").on("click", function () {
        $(".sidebar-sticky-item").fadeIn().addClass("active");
    });

    
      /* ================================
       Sticky Header Js Start
    ================================ */

       $windowOn.on("scroll", function () {
        if ($(this).scrollTop() > 250) {
          $("#header-sticky").addClass("sticky");
        } else {
          $("#header-sticky").removeClass("sticky");
        }
      });      


      ////////////////////////////////////////////////////
	// 05. Search Js
	$(".search_btn").on("click", function () {
		$(".search_popup").addClass("search-opened");
		$(".search-popup-overlay").addClass("search-popup-overlay-open");
		$("body").addClass("overflow-hidden");
	});

	$(".search_close_btn").on("click", function () {
		$(".search_popup").removeClass("search-opened");
		$(".search-popup-overlay").removeClass("search-popup-overlay-open");
		$("body").removeClass("overflow-hidden");
	});
	$(".search-popup-overlay").on("click", function () {
		$(".search_popup").removeClass("search-opened");
		$(this).removeClass("search-popup-overlay-open");
		$("body").removeClass("overflow-hidden");
	});

      
       /* ================================
       Video & Image Popup Js Start
    ================================ */

      $(".img-popup").magnificPopup({
        type: "image",
        gallery: {
          enabled: true,
        },
      });

      $(".video-popup").magnificPopup({
        type: "iframe",
        callbacks: {},
      });
  
      /* ================================
       Counterup Js Start
    ================================ */

      $(".count").counterUp({
        delay: 15,
        time: 4000,
      });
  
      /* ================================
       Wow Animation Js Start
    ================================ */

      new WOW().init();
  
      /* ================================
       Nice Select Js Start
    ================================ */

    if ($('.single-select').length) {
        $('.single-select').niceSelect();
    }

      /* ================================
       Parallaxie Js Start
    ================================ */

      if ($('.parallaxie').length && $(window).width() > 991) {
          if ($(window).width() > 768) {
              $('.parallaxie').parallaxie({
                  speed: 0.55,
                  offset: 0,
              });
          }
      }


    

    /* ================================
     Scrolldown Js Start
    ================================ */
    $("#scrollDown").on("click", function () {
        setTimeout(function () {
            $("html, body").animate({ scrollTop: "+=1000px" }, "slow");
        }, 1000);
    });


     /* ================================
      Hover Active Js Start
    ================================ */

    $(".feature-box-item-2").hover(
        function () {
            $(".feature-box-item-2").removeClass("active");
            $(this).addClass("active");
        }
    );

     $(".process-card").hover(
        function () {
            $(".process-card").removeClass("active");
            $(this).addClass("active");
        }
    );

    $(".count-item-2").hover(
        function () {
            $(".count-item-2").removeClass("active");
            $(this).addClass("active");
        }
    );

    $(".count-item").hover(
        function () {
            $(".count-item").removeClass("active");
            $(this).addClass("active");
        }
    );

    /* ================================
      Global Service Box Js Start
    ================================ */

    const serviceItems = document.querySelectorAll(".service-item");

    serviceItems.forEach((box) => {
    const hoverImg = box.querySelector(".hover-image");
    if (!hoverImg) return;

    box.addEventListener("mousemove", (e) => {
        const rect = box.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        hoverImg.style.opacity = "1";
        hoverImg.style.visibility = "visible";
        hoverImg.style.transform = `translate(${x}px, ${y}px) rotate(0deg)`;
    });

    box.addEventListener("mouseleave", () => {
        hoverImg.style.opacity = "0";
        hoverImg.style.visibility = "hidden";
    });
    });

    //>> Project Hover Js Start <<//
    const getSlide = $('.main-box, .box-2').length - 1;
    const slideCal = 100 / getSlide + '%';
    
    $('.box-2').css({
        "width": slideCal
    });
    
    $(document).on('mouseenter', '.box-2', function() {
        $('.box-2').removeClass('active');
        $(this).addClass('active');
    });


    // Data background support
    document.querySelectorAll('[data-background]').forEach(function (el) {
        const bg = el.getAttribute('data-background');
        if (bg) {
            el.style.backgroundImage = `url(${bg})`;
        }
    });


    (function () {
        var $slides = document.querySelectorAll('.hero-portfolio-revealing-slide');
        var $controls = document.querySelectorAll('.hero-portfolio-revealing-slider-control');
        var $pagination = document.querySelector('.dot-number'); // pagination container
        var numOfSlides = $slides.length;
        var slidingAT = 1300;
        var slidingBlocked = false;

        // Assign slide numbers and classes
        [].slice.call($slides).forEach(function ($el, index) {
            var i = index + 1;
            $el.classList.add('hero-portfolio-revealing-slide-' + i);
            $el.dataset.slide = i;
        });

        if (!$slides.length) return;

        $slides[0].classList.add('s-active');

        // Build pagination bullets dynamically
        if ($pagination) {
            $pagination.innerHTML = '';
            [].slice.call($slides).forEach(function ($el, index) {
                var dotNum = $el.querySelector('.dot-num')?.outerHTML || (index + 1);
                var span = document.createElement('span');
                span.classList.add('swiper-pagination-bullet');
                if (index === 0) span.classList.add('swiper-pagination-bullet-active');
                span.innerHTML = dotNum;
                span.dataset.index = index + 1;
                span.addEventListener('click', function () {
                    if (slidingBlocked) return;
                    changeSlideTo(+this.dataset.index);
                });
                $pagination.appendChild(span);
            });
        }

        // Controls click
        [].slice.call($controls).forEach(function ($el) {
            $el.addEventListener('click', controlClickHandler);
        });

        function controlClickHandler() {
            if (slidingBlocked) return;
            var isRight = this.classList.contains('m-right');
            changeSlide(isRight, this);
        }

        function changeSlide(isRight, $controlEl) {
            var $curActive = document.querySelector('.hero-portfolio-revealing-slide.s-active');
            if (!$curActive) return;

            slidingBlocked = true;

            var index = +$curActive.dataset.slide;
            isRight ? index++ : index--;
            if (index < 1) index = numOfSlides;
            if (index > numOfSlides) index = 1;

            changeSlideTo(index, $controlEl, isRight);
        }

        function changeSlideTo(index, $controlEl, isRight = true) {
            var $curActive = document.querySelector('.hero-portfolio-revealing-slide.s-active');
            var $newActive = document.querySelector('.hero-portfolio-revealing-slide-' + index);

            if ($controlEl) $controlEl.classList.add('a-rotation');

            $curActive.classList.remove('s-active', 's-active-prev');
            document.querySelector('.hero-portfolio-revealing-slide.s-prev')?.classList.remove('s-prev');

            $newActive.classList.add('s-active');
            if (!isRight) $newActive.classList.add('s-active-prev');

            var prevIndex = index - 1;
            if (prevIndex < 1) prevIndex = numOfSlides;
            document.querySelector('.hero-portfolio-revealing-slide-' + prevIndex).classList.add('s-prev');

            // Animate headings
            var direction = isRight ? 1 : -1;
            var currentHeading = $curActive.querySelector('.hero-portfolio-revealing-slide-heading');
            var nextHeading = $newActive.querySelector('.hero-portfolio-revealing-slide-heading');

            if ($slides && $slides.length > 0 && $newActive) {
           
            $slides.forEach(slide => {
                const heading = slide.querySelector('.hero-portfolio-revealing-slide-heading');
                if (heading) {
                    gsap.set(heading, { clipPath: "inset(0 100% 0 0)" });
                }
            });

            const nextHeading = $newActive.querySelector('.hero-portfolio-revealing-slide-heading');
            if (nextHeading) {
                gsap.to(nextHeading, {
                    clipPath: "inset(0 0% 0 0)",
                    duration: 0.8,
                    ease: "power3.out"
                });
            }
        }



            // Update pagination active state
            if ($pagination) {
                var bullets = $pagination.querySelectorAll('.swiper-pagination-bullet');
                bullets.forEach(b => b.classList.remove('swiper-pagination-bullet-active'));
                bullets[index - 1]?.classList.add('swiper-pagination-bullet-active');
            }

            setTimeout(function () {
                if ($controlEl) $controlEl.classList.remove('a-rotation');
                slidingBlocked = false;
            }, slidingAT * 0.75);
        }

    })();



    /* ================================
      Brand Slider Js Start
    ================================ */

    if ($('.brand-slider').length > 0) {
        const brandSlider = new Swiper(".brand-slider", {
            spaceBetween: 30,
            speed: 1300,
            centeredSlides: true,
            loop: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
        
            breakpoints: {
                1399: {
                    slidesPerView: 7,
                },
                1199: {
                    slidesPerView: 5,
                },
                991: {
                    slidesPerView: 4,
                },
                767: {
                    slidesPerView: 3,
                },
                575: {
                    slidesPerView: 2,
                },
                0: {
                    slidesPerView: 2,
                },
            },
        });
    }

    /* ================================
      Team Slider Js Start
    ================================ */
   if ($('.team-slider').length > 0) {
    const TeamSlider = new Swiper(".team-slider", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        navigation: {
            nextEl: ".array-next",
            prevEl: ".array-prev",
        },
        breakpoints: {
            1399: {
                slidesPerView: 4,
            },
            1199: {
                slidesPerView: 3,
            },
            991: {
                slidesPerView: 2,
            },
            767: {
                slidesPerView: 2,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }

   /* ================================
      Team Slider Js Start
    ================================ */
   if ($('.team-slider-2').length > 0) {
    const TeamSlider2 = new Swiper(".team-slider-2", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        centeredSlides: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        navigation: {
            nextEl: ".array-next",
            prevEl: ".array-prev",
        },
        breakpoints: {
            1399: {
                slidesPerView: 3,
            },
            1199: {
                slidesPerView: 2,
            },
            991: {
                slidesPerView: 2,
            },
            767: {
                slidesPerView: 2,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }

   //>> Hero-Image Slider Start <<//
       if($('.service-image-slider').length > 0) {
            const ServiceImageSlider = new Swiper(".service-image-slider", {
                spaceBetween: 30,
                speed: 2000,
                loop: true,
                 pagination: {
                    el: ".dot2",
                    clickable: true,
                },
                    autoplay: {
                    delay: 1,
                    disableOnInteraction: true,
                },
            });
        }

    /* ================================
      Testimonial Slider Js Start
    ================================ */

   if ($('.testimonial-slider').length > 0) {
    const TestimonialSlider = new Swiper(".testimonial-slider", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        navigation: {
            nextEl: ".array-next",
            prevEl: ".array-prev",
        },
        breakpoints: {
            1199: {
                slidesPerView: 3,
            },
            991: {
                slidesPerView: 2,
            },
            767: {
                slidesPerView: 2,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }

   /* ================================
      Testimonial Slider Js Start
    ================================ */

   if ($('.testimonial-slider-2').length > 0) {
    const TestimonialSlider2 = new Swiper(".testimonial-slider-2", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        navigation: {
            nextEl: ".array-next",
            prevEl: ".array-prev",
        },
        breakpoints: {
            1199: {
                slidesPerView: 1,
            },
            991: {
                slidesPerView: 1,
            },
            767: {
                slidesPerView: 1,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }
   

   /* ================================
      Testimonial Slider Js Start
    ================================ */

   if ($('.testimonial-slider-3').length > 0) {
    const TestimonialSlider3 = new Swiper(".testimonial-slider-3", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        navigation: {
            nextEl: ".array-next",
            prevEl: ".array-prev",
        },
        breakpoints: {
            1199: {
                slidesPerView: 2,
            },
            991: {
                slidesPerView: 1,
            },
            767: {
                slidesPerView: 1,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }
   
    

  


   /* ================================
      News Slider Js Start
    ================================ */

   if ($('.news-slider').length > 0) {
    const NewsSlider = new Swiper(".news-slider", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        pagination: {
            el: ".dot",
            clickable: true,
        },
        breakpoints: {
            1399: {
                slidesPerView: 4,
            },
            1199: {
                slidesPerView: 3,
            },
            991: {
                slidesPerView: 2,
            },
            767: {
                slidesPerView: 1,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }

   /* ================================
      Choose-us Slider Js Start
    ================================ */

   if ($('.choose-us-slider').length > 0) {
    const ChooseUsSlider = new Swiper(".choose-us-slider", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        breakpoints: {
            1399: {
                slidesPerView: 5,
            },
            1199: {
                slidesPerView: 4,
            },
            991: {
                slidesPerView: 3,
            },
            767: {
                slidesPerView: 2,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }

   /* ================================
      Service-Slider Js Start
    ================================ */

   if ($('.service-slider').length > 0) {
    const ServiceSlider = new Swiper(".service-slider", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        navigation: {
            nextEl: ".array-next",
            prevEl: ".array-prev",
        },
        breakpoints: {
            1399: {
                slidesPerView: 3,
            },
            1199: {
                slidesPerView: 2,
            },
            991: {
                slidesPerView: 2,
            },
            767: {
                slidesPerView: 2,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }

   /* ================================
      Service-Slider Js Start
    ================================ */

   if ($('.drone-slider').length > 0) {
    const DroneSlider = new Swiper(".drone-slider", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        centeredSlides: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        navigation: {
            nextEl: ".array-next",
            prevEl: ".array-prev",
        },
        breakpoints: {
            1399: {
                slidesPerView: 3,
            },
            1199: {
                slidesPerView: 2,
            },
            991: {
                slidesPerView: 2,
            },
            767: {
                slidesPerView: 2,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
   }

  /* ================================
    Marquee-Group Js Start
    ================================ */

    if (document.querySelectorAll(".marquee-group").length) {
        const marqueegroup = document.querySelectorAll(".marquee-group");

        marqueegroup.forEach((box) => {
            const hoverImg = box.querySelector(".hover-image");
            if (!hoverImg) return;

            box.addEventListener("mousemove", (event) => {
            const rect = box.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            hoverImg.style.opacity = "1";
            hoverImg.style.visibility = "visible";
            hoverImg.style.transform = `translate(${x}px, ${y}px) rotate(10deg)`;
            });

            box.addEventListener("mouseleave", () => {
            hoverImg.style.opacity = "0";
            hoverImg.style.visibility = "hidden";
            hoverImg.style.transform = `translateY(-50%) rotate(10deg)`;
            });
        });
        }

        
         //>> Quantity Js Start <<//
    $(".quantity").on("click", ".plus", function () {
        let $input = $(this).prev("input.qty");
        let val = parseInt($input.val() || 0, 10); // Ensure valid number
        $input.val(val + 1).change();
    });

    $(".quantity").on("click", ".minus", function () {
        let $input = $(this).next("input.qty");
        let val = parseInt($input.val() || 0, 10); // Ensure valid number
        if (val > 1) { // Prevent negative values if needed
            $input.val(val - 1).change();
        }
    });

    //>> Quantity Cart Js Start <<//
    const quantity = 0;
    const price = 0;
    $(".cart-item-quantity-amount, .product-quant").html(quantity);
    $(".total-price, .product-pri").html(price.toFixed(2));
    $(".cart-increment, .cart-incre").on("click", function() {
        if (quantity <= 4) {
            quantity++;
            $(".cart-item-quantity-amount, .product-quant").html(quantity);
            let basePrice = $(".base-price, .base-pri").text();
            $(".total-price, .product-pri").html((basePrice * quantity).toFixed(2));
        }
    });

    $(".cart-decrement, .cart-decre").on("click", function() {
        if (quantity >= 1) {
            quantity--;
            $(".cart-item-quantity-amount, .product-quant").html(quantity);
            let basePrice = $(".base-price, .base-pri").text();
            $(".total-price, .product-pri").html((basePrice * quantity).toFixed(2));
        }
    });

    $(".cart-item-remove>a").on("click", function() {
        $(this).closest(".cart-item").hide(300);
    });

     // Quantity increment and decrement
    const quantityIncrement = document.querySelectorAll(".quantityIncrement");
    const quantityDecrement = document.querySelectorAll(".quantityDecrement");

    if (quantityIncrement.length && quantityDecrement.length) {
        quantityIncrement.forEach((increment) => {
            increment.addEventListener("click", function () {
                const input = increment.parentElement.querySelector("input");
                const value = parseInt(input.value || 0, 10); // Ensure valid number
                input.value = value + 1;
            });
        });

        quantityDecrement.forEach((decrement) => {
            decrement.addEventListener("click", function () {
                const input = decrement.parentElement.querySelector("input");
                const value = parseInt(input.value || 0, 10); // Ensure valid number
                if (value > 1) {
                    input.value = value - 1;
                }
            });
        });
    }
 

    /* ================================
      Custom Accordion Js Start
    ================================ */

   if ($('.accordion-box').length) {
        $(".accordion-box").on('click', '.acc-btn', function () {
            var outerBox = $(this).closest('.accordion-box');
            var target = $(this).closest('.accordion');
            var accBtn = $(this);
            var accContent = accBtn.next('.acc-content');

            if (target.hasClass('active-block')) {
                // Already open, so close it
                accBtn.removeClass('active');
                target.removeClass('active-block');
                accContent.slideUp(300);
            } else {
                // Close all others
                outerBox.find('.accordion').removeClass('active-block');
                outerBox.find('.acc-btn').removeClass('active');
                outerBox.find('.acc-content').slideUp(300);

                // Open clicked one
                accBtn.addClass('active');
                target.addClass('active-block');
                accContent.slideDown(300);
            }
        });
    }

    /* ================================
        Mouse Cursor Animation Js Start
    ================================ */

    if ($(".mouseCursor").length > 0) {
        function itCursor() {
            var myCursor = jQuery(".mouseCursor");
            if (myCursor.length) {
                if ($("body")) {
                    const e = document.querySelector(".cursor-inner"),
                        t = document.querySelector(".cursor-outer");
                    let n, i = 0, o = !1;
                    window.onmousemove = function(s) {
                        if (!o) {
                            t.style.transform = "translate(" + s.clientX + "px, " + s.clientY + "px)";
                        }
                        e.style.transform = "translate(" + s.clientX + "px, " + s.clientY + "px)";
                        n = s.clientY;
                        i = s.clientX;
                    };
                    $("body").on("mouseenter", "button, a, .cursor-pointer", function() {
                        e.classList.add("cursor-hover");
                        t.classList.add("cursor-hover");
                    });
                    $("body").on("mouseleave", "button, a, .cursor-pointer", function() {
                        if (!($(this).is("a", "button") && $(this).closest(".cursor-pointer").length)) {
                            e.classList.remove("cursor-hover");
                            t.classList.remove("cursor-hover");
                        }
                    });
                    e.style.visibility = "visible";
                    t.style.visibility = "visible";
                }
            }
        }
        itCursor();
    }

    /* ================================
        Back To Top Button Js Start
    ================================ */
    $windowOn.on('scroll', function() {
        var windowScrollTop = $(this).scrollTop();
        var windowHeight = $(window).height();
        var documentHeight = $(document).height();

        if (windowScrollTop + windowHeight >= documentHeight - 10) {
            $("#back-top").addClass("show");
        } else {
            $("#back-top").removeClass("show");
        }
    });

    $documentOn.on('click', '#back-top', function() {
        $('html, body').animate({ scrollTop: 0 }, 800);
        return false;
    });

    /* ================================
       Search Popup Toggle Js Start
    ================================ */

    // if ($(".search-toggler").length) {
    //     $(".search-toggler").on("click", function(e) {
    //         e.preventDefault();
    //         $(".search-popup").toggleClass("active");
    //         $("body").toggleClass("locked");
    //     });
    // }
	
    /* ================================
       Smooth Scroller And Title Animation Js Start
    ================================ */
    if ($('#smooth-wrapper').length && $('#smooth-content').length) {
        gsap.registerPlugin(ScrollTrigger, ScrollSmoother, SplitText);

        gsap.config({
            nullTargetWarn: false,
        });

        let smoother = ScrollSmoother.create({
            wrapper: "#smooth-wrapper",
            content: "#smooth-content",
            smooth: 2,
            effects: true,
            smoothTouch: 0.1,
            normalizeScroll: false,
            ignoreMobileResize: true,
        });
    }

     /* ================================
       Sticky Js Start
    ================================ */


    /* ================================
       Text Anim Js Start
    ================================ */

   if ($(".text-anim").length) {
        let staggerAmount = 0.03,
            translateXValue = 20,
            delayValue = 0.1,
            easeType = "power2.out",
            animatedTextElements = document.querySelectorAll(".text-anim");

        animatedTextElements.forEach(element => {
            let animationSplitText = new SplitText(element, { type: "chars, words" });

            // ScrollTrigger দিয়ে section এ ঢুকলে animation শুরু হবে
            ScrollTrigger.create({
                trigger: element,
                start: "top 85%",
                onEnter: () => {
                    gsap.from(animationSplitText.chars, {
                        duration: 1,
                        delay: delayValue,
                        x: translateXValue,
                        autoAlpha: 0,
                        stagger: staggerAmount,
                        ease: easeType,
                    });
                },
            });
        });
    }

    if($('.tz-itm-title').length) {
		var txtheading = $(".tz-itm-title");

    if(txtheading.length == 0) return; gsap.registerPlugin(SplitText); txtheading.each(function(index, el) {

        el.split = new SplitText(el, {
          type: "lines,words,chars",
          linesClass: "split-line"
        });

        if( $(el).hasClass('tz-itm-anim') ){
          gsap.set(el.split.chars, {
            opacity: .3,
            x: "-7",
          });
        }
        el.anim = gsap.to(el.split.chars, {
          scrollTrigger: {
            trigger: el,
            start: "top 92%",
            end: "top 60%",
            markers: false,
            scrub: 1,
          },

          x: "0",
          y: "0",
          opacity: 1,
          duration: .7,
          stagger: 0.2,
        });

      });
    }

    // image animation
    let revealContainers = document.querySelectorAll(".reveal");

    revealContainers.forEach((container) => {
        let image = container.querySelector("img");
        let tl = gsap.timeline({
        scrollTrigger: {
            trigger: container,
            toggleActions: "restart none none reset"
        }
        });

        tl.set(container, { autoAlpha: 1 });
        tl.from(container, 1.5, {
        xPercent: -100,
        ease: Power2.out
        });
        tl.from(image, 1.5, {
        xPercent: 100,
        scale: 1.3,
        delay: -1.5,
        ease: Power2.out
        });
    });


    gsap.registerPlugin(ScrollTrigger);

    // 992px এর উপরে স্ক্রল পিন চালু হবে
    ScrollTrigger.matchMedia({
    
    "(min-width: 1199px)": function () {
        let projectPanels = document.querySelectorAll('.project-panel');

        projectPanels.forEach((section) => {
        gsap.to(section, {
            scrollTrigger: {
            trigger: section,
            pin: section,
            scrub: 1,
            start: "top 10%",
            end: "bottom 65%",
            endTrigger: ".project-panel-area",
            pinSpacing: false,
            markers: false
            }
        });
        });
    },

    // 991px এবং নিচে - সব ScrollTrigger বন্ধ
    "(max-width: 1199px)": function () {
        ScrollTrigger.getAll().forEach(st => st.kill());
    }

    });


  /* ==================================================
    Image Scale
    ================================================== */
   var width = $(window).width();

    if (width > 1023) {
        if (document.querySelectorAll(".scale-animation").length > 0) {

            gsap.registerPlugin(ScrollTrigger);

            gsap.utils.toArray(".scale-animation").forEach(function (section) {

                gsap.timeline({
                    scrollTrigger: {
                        trigger: section,
                        scrub: 3,
                        start: "top 90%",
                        end: "bottom 70%",
                    },
                })
                .from(section, {
                    scale: 0.8,
                    opacity: 0,
                    transformOrigin: "center bottom",
                    duration: 1.5,
                    ease: "power2.out",
                })
                .to(section, {
                    scale: 1,
                    opacity: 1,
                    transformOrigin: "center bottom",
                    duration: 1.2,
                    ease: "power2.out",
                });
            });
        }
    }

  if ($('.full-img-wrap3').length > 0) {
        // Check window width
        if (window.innerWidth > 1399) {
            ScrollTrigger.create({
                trigger: ".full-img-wrap3",
                start: "top 0",
                end: "bottom 0%",
                pin: ".full-img3",
                pinSpacing: false,
            });
        }
    }


    // ScrollTrigger register করতে ভুলবেন না
    gsap.registerPlugin(ScrollTrigger);

    gsap.utils.toArray(".tp_fade_anim").forEach((item) => {
        let tp_fade_offset = item.getAttribute("data-fade-offset") || 40,
            tp_duration_value = item.getAttribute("data-duration") || 0.75,
            tp_fade_direction = item.getAttribute("data-fade-from") || "bottom",
            tp_onscroll_value = item.getAttribute("data-on-scroll") || 1,
            tp_delay_value = item.getAttribute("data-delay") || 0.15,
            tp_ease_value = item.getAttribute("data-ease") || "power2.out";

        let tp_anim_setting = {
            opacity: 0,
            ease: tp_ease_value,
            duration: tp_duration_value,
            delay: tp_delay_value,
            x: (tp_fade_direction == "left" ? -tp_fade_offset : (tp_fade_direction == "right" ? tp_fade_offset : 0)),
            y: (tp_fade_direction == "top" ? -tp_fade_offset : (tp_fade_direction == "bottom" ? tp_fade_offset : 0)),
        };

        // Scroll এ animate হবে
        if (tp_onscroll_value == 1) {
            tp_anim_setting.scrollTrigger = {
                trigger: item,
                start: "top 85%",
                toggleActions: "play none none reset",
            };
        }

        gsap.from(item, tp_anim_setting);
    });

   
    /* ==================================================
     Text Anim  Image 
    ================================================== */
    const textAnims = document.querySelectorAll('.text-anims');

    const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if(entry.isIntersecting){
        entry.target.classList.add('show');
        observer.unobserve(entry.target); // একবার হলে আর observe করবে না
        }
    });
    }, { threshold: 0.5 }); // 50% দেখা গেলে trigger

    textAnims.forEach(el => observer.observe(el));


    // Create mask divs for each wrapper
		
        document.querySelectorAll(".tp-clip-anim").forEach(wrapper => {
        const img = wrapper.querySelector(".tp-anim-img[data-animate='true']");
        if (!img) return;
        const url = img.src;

        // ensure wrapper position relative
        wrapper.style.position = "relative";

        // IntersectionObserver
        const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
        if (entry.isIntersecting) {
        wrapper.querySelectorAll(".mask").forEach(m => m.remove());

            // Create 9 masks
            for (let i = 0; i < 9; i++) {
                const mask = document.createElement("div");
                mask.className = `mask mask-${i + 1}`;
                Object.assign(mask.style, {
                    backgroundImage: `url(${url})`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                    position: "absolute",
                    inset: "0"
                });
                wrapper.appendChild(mask);
            }

            // observer stop
            obs.unobserve(entry.target);
        }
    });
        }, { threshold: 0.2 });

        observer.observe(wrapper);
        });

        // scale animation 
        var scale = document.querySelectorAll(".scale");
        var image = document.querySelectorAll(".scale img");
        scale.forEach((item) => {
            gsap.to(item, {
            scale: 1,
            duration: 1,
            ease: "power1.out",
            scrollTrigger: {
                trigger: item,
                start: 'top bottom',
                end: "bottom top",
                toggleActions: 'play reverse play reverse'
            }
            });
        });
        image.forEach((image) => {
            gsap.set(image, {
            scale: 1.3,
            });
            gsap.to(image, {
            scale: 1,
            duration: 1,
            scrollTrigger: {
                trigger: image,
                start: 'top bottom',
                end: "bottom top",
                toggleActions: 'play reverse play reverse'
            }
            });
        })


        // Project-card-wrapper-4 animation 
        gsap.utils.toArray(".project-card-wrapper-4 .project-card-items-4").forEach((element, index, array) => {
        if (index === array.length - 1) return;

            const delay = parseFloat(element.getAttribute("data-ani-delay")) || 0;
            gsap.to(element, {
                scale: .6,
                opacity: 0,
                duration: 2,
                delay: delay,
                scrollTrigger: {
                    trigger: element,
                    start: "top 15%",
                    end: "bottom 15%",
                    scrub: 2,
                    pin: true,
                    pinSpacing: false,
                    markers: false
                }
            });
        });

    /* ================================
       Title SplitText Js Start
    ================================ */
   
    if ($('.wt-about-title2').length > 0) {

    let cta = gsap.timeline({
        repeat: -1,
        delay: 0.5,
        scrollTrigger: {
            trigger: '.wt-about-title2',
            start: 'bottom 100%-=50px'
        }
    });

    // Initial style
    gsap.set('.wt-about-title2 .animated-img', {
        opacity: 0,
        scale: 1
    });

    // Fade in on scroll
    gsap.to('.wt-about-title2 .animated-img', {
        opacity: 1,
        duration: 1,
        ease: 'power1.out',
        scrollTrigger: {
            trigger: '.wt-about-title2',
            start: 'bottom 100%-=50px',
            once: true
        }
    });

    // Main animation loop
    cta.to('.wt-about-title2 .animated-img', {
        duration: 0.5,
        scaleY: 0.9,
        ease: "power1.out",
    });
    cta.to('.wt-about-title2 .animated-img', {
        y: -20,
        rotation: 1,
        ease: "elastic.out(1, 0.3)",
        duration: 0.8
    }, 0.5);
    cta.to('.wt-about-title2 .animated-img', {
        scaleY: 1,
        rotation: 0,
        ease: "elastic.out(1, 0.3)",
        duration: 1.5
    }, 0.5);
    cta.to('.wt-about-title2 .animated-img', {
        filter: "brightness(1.2) saturate(1.5)",
        ease: "power1.out",
        duration: 0.5
    }, 0.5);
    cta.to('.wt-about-title2 .animated-img', {
        y: 0,
        scale: 1,
        rotation: 0,
        filter: "brightness(1) saturate(1)",
        ease: "back.out(1.7)",
        duration: 0.8
    }, 0.7);

    }


    gsap.registerPlugin(ScrollTrigger);

    const wrapper = document.querySelector(".project-wrapper-2");
    const leftItems = gsap.utils.toArray(".project-left-item .project-image");
    const rightImages = gsap.utils.toArray(".project-thumb .thumb-img");
    const numberEl = document.querySelector(".project-thumb h2");

    if (wrapper && leftItems.length === rightImages.length) {

        activateProject(0);

        ScrollTrigger.create({
            trigger: wrapper,
            start: "top 10%",
            end: "+=" + (leftItems.length - 1) * window.innerHeight,
            pin: true,
            snap: {
                snapTo: 1 / (leftItems.length - 1),
                duration: 0.1,
                ease: "none"
            },
            onUpdate: self => {
                const index = Math.round(
                    self.progress * (leftItems.length - 1)
                );
                activateProject(index);
            }
        });

        function activateProject(activeIndex) {

            rightImages.forEach(img => img.classList.remove("active"));
            rightImages[activeIndex].classList.add("active");

            leftItems.forEach(item => {
                const dot = item.querySelector("span");
                const link = item.querySelector("h3 a");
                if (dot) dot.style.backgroundColor = "#fff";
                if (link) link.style.color = "#fff";
            });

            const activeItem = leftItems[activeIndex];
            if (activeItem) {
                const dot = activeItem.querySelector("span");
                const link = activeItem.querySelector("h3 a");
                if (dot) dot.style.backgroundColor = "#F5D83E";
                if (link) link.style.color = "#F5D83E";
            }

            if (numberEl) {
                numberEl.textContent = String(activeIndex + 1).padStart(2, "0");
            }
        }
    }


    gsap.utils.toArray(" .item_right_1").forEach((el, index) => {
        let tlcta = gsap.timeline({
            scrollTrigger: {
                trigger: el,
                scrub: 2,
                start: "top 90%",
                end: "top 70%",
                toggleActions: "play none none reverse",
                markers: false,
            },
        });

        tlcta
            .set(el, { transformOrigin: "center center" })
            .from(
                el,
                { opacity: 1, x: "+=365" },
                { opacity: 1, x: 0, duration: 1, immediateRender: false }
            );
    });

    gsap.utils.toArray(" .item_left_1").forEach((el, index) => {
    let tlcta = gsap.timeline({
    scrollTrigger: {
        trigger: el,
        scrub: 2,
        start: "top 90%",
        end: "top 70%",
        toggleActions: "play none none reverse",
        markers: false,
    },
    });

    tlcta
    .set(el, { transformOrigin: "center center" })
    .from(
        el,
        { opacity: 1, x: "-=365" },
        { opacity: 1, x: 0, duration: 1, immediateRender: false }
    );
    });

     
    // Project-card-wrapper-4 animation 
        gsap.utils.toArray(".news-card-wrapper .news-card-items-5").forEach((element, index, array) => {
        if (index === array.length - 1) return;

            const delay = parseFloat(element.getAttribute("data-ani-delay")) || 0;
            gsap.to(element, {
                scale: .6,
                opacity: 0,
                duration: 2,
                delay: delay,
                scrollTrigger: {
                    trigger: element,
                    start: "top 15%",
                    end: "bottom 15%",
                    scrub: 2,
                    pin: true,
                    pinSpacing: false,
                    markers: false
                }
            });
        });
    


        



    
    }); // End Document Ready Function

   


    // Year Change ANimatoin
    document.addEventListener("DOMContentLoaded", function () {

    gsap.registerPlugin(ScrollTrigger);

    const years = document.querySelectorAll(".year-list h2");
    const image = document.getElementById("historyImage");
    const total = years.length;

    let currentIndex = -1;

    gsap.timeline({
        scrollTrigger: {
        trigger: ".our-history-wrapper",
        start: "top 15%",
        end: "+=" + total * 100 + "%",
        scrub: true,
        pin: true,
        pinSpacing: true,
        anticipatePin: 1,
        onUpdate: (self) => {

            // 🔹 progress থেকে index বের করা
            const index = Math.floor(self.progress * total);

            if (index !== currentIndex && years[index]) {
            currentIndex = index;

            // active year
            years.forEach(y => y.classList.remove("active"));
            years[index].classList.add("active");

            // image change
            const img = years[index].dataset.img;
            if (img) {
                gsap.to(image, { opacity: 0, duration: 0.25 });

                setTimeout(() => {
                image.src = img;
                gsap.to(image, { opacity: 1, duration: 0.4 });
                }, 250);
            }
            }
        }
        }
    });

    });


    
  // Image Trail ANimatoin
    document.addEventListener("DOMContentLoaded", () => {

    const sections = document.querySelectorAll(".image-trail-animation");
    if (!sections.length) return;

    const MathUtils = {
        lerp: (a, b, n) => (1 - n) * a + n * b,
        distance: (x1, y1, x2, y2) => Math.hypot(x2 - x1, y2 - y1)
    };

    sections.forEach(section => {

        const imagesWrapper = section.querySelector(".image-trail-images");
        if (!imagesWrapper) return;

        const images = [...imagesWrapper.querySelectorAll("img")];

        let mouse = { x: 0, y: 0 };
        let lastMouse = { x: 0, y: 0 };
        let cachedMouse = { x: 0, y: 0 };

        const threshold = 80;
        let zIndex = 1;
        let imgIndex = 0;

        const getMousePos = (e) => {
        const rect = section.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        };

        section.addEventListener("mousemove", (e) => {
        mouse = getMousePos(e);
        });

        class ImageTrail {
        constructor() {
            requestAnimationFrame(() => this.render());
        }

        render() {
            const distance = MathUtils.distance(
            mouse.x, mouse.y,
            lastMouse.x, lastMouse.y
            );

            cachedMouse.x = MathUtils.lerp(
            cachedMouse.x || mouse.x,
            mouse.x,
            0.15
            );
            cachedMouse.y = MathUtils.lerp(
            cachedMouse.y || mouse.y,
            mouse.y,
            0.15
            );

            if (distance > threshold) {
            this.showImage();
            lastMouse = { ...mouse };
            }

            requestAnimationFrame(() => this.render());
        }

        showImage() {
            const img = images[imgIndex];
            if (!img) return;

            gsap.killTweensOf(img);

            const rect = img.getBoundingClientRect();

            gsap.set(img, {
            opacity: 1,
            scale: 1,
            zIndex: zIndex++,
            x: cachedMouse.x - rect.width / 2,
            y: cachedMouse.y - rect.height / 2
            });

            gsap.to(img, {
            duration: 0.8,
            ease: "expo.out",
            x: mouse.x - rect.width / 2,
            y: mouse.y - rect.height / 2
            });

            gsap.to(img, {
            duration: 0.9,
            delay: 0.3,
            opacity: 0,
            scale: 0.25,
            ease: "power2.out"
            });

            imgIndex = (imgIndex + 1) % images.length;
        }
        }

        new ImageTrail();
    });
    });


    /* ================================
       Mous Slide Js Start
    ================================ */
    document.addEventListener('DOMContentLoaded', () => {
    const galleryWrapper = document.querySelector('.gallery-wrapper');
    if (!galleryWrapper) return; 

    const galleryTrack = document.querySelector('.gallery-track');
    const dragCircle = document.querySelector('.drag-circle');

    let trackX = 0;
    let lastCursorX = null;

    galleryWrapper.addEventListener('mousemove', (e) => {
        const rect = galleryWrapper.getBoundingClientRect();
        const cursorX = e.clientX - rect.left;
        const cursorY = e.clientY - rect.top;

        dragCircle.style.left = cursorX + 'px';
        dragCircle.style.top = cursorY + 'px';

        if (lastCursorX !== null) {
            const deltaX = cursorX - lastCursorX;
            trackX += deltaX;

            const maxTranslate = 0;
            const minTranslate = Math.min(
                galleryWrapper.clientWidth - galleryTrack.scrollWidth,
                0
            );

            if (trackX > maxTranslate) trackX = maxTranslate;
            if (trackX < minTranslate) trackX = minTranslate;

            galleryTrack.style.transform = `translateX(${trackX}px)`;
        }

        lastCursorX = cursorX;
    });

    galleryWrapper.addEventListener('mouseleave', () => {
        lastCursorX = null;
    });
});


    window.addEventListener("load", function () {
        const preloader = document.getElementById("agri-preloader");

        // fade out almost instantly
        setTimeout(() => {
            preloader.style.transition = "opacity 0.15s ease";
            preloader.style.opacity = "0";
        }, 500);

        // fully remove
        setTimeout(() => {
            preloader.style.display = "none";
        }, 500);
    });

    
  })(jQuery); // End jQuery

