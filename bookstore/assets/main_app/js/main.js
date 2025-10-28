lucide.createIcons();
	
document.body.addEventListener('htmx:configRequest', function (event) {
	const csrf = document.querySelector('input[name="csrfmiddlewaretoken"]');
	if (csrf) {
	event.detail.headers['X-CSRFToken'] = csrf.value;
	}
});
function initProductSliders() {
	if (!window.Swiper) {
	return;
	}
	document.querySelectorAll('[data-banner-id]').forEach(function (bannerRoot) {
	const mainSlider = bannerRoot.querySelector('.js-banner-slider');
	if (!mainSlider || mainSlider.dataset.sliderInitialized === 'true') {
		return;
	}
	const thumbsEl = bannerRoot.querySelector('.js-banner-thumbs');
	let thumbsSwiper = null;
	if (thumbsEl && thumbsEl.dataset.sliderInitialized !== 'true') {
		thumbsSwiper = new Swiper(thumbsEl, {
		slidesPerView: 4,
		spaceBetween: 12,
		freeMode: true,
		watchSlidesProgress: true,
		breakpoints: {
			1280: { slidesPerView: 7 },
		}
		});
		thumbsEl.dataset.sliderInitialized = 'true';
	}
	const bannerOptions = {
		slidesPerView: 1,
		loop: true,
		autoplay: {
		delay: 4800,
		disableOnInteraction: false
		},
		speed: 1400,
		spaceBetween: 30
	};
	if (thumbsSwiper) {
		bannerOptions.thumbs = { swiper: thumbsSwiper };
	}
	const prev = bannerRoot.querySelector('.js-banner-prev');
	const next = bannerRoot.querySelector('.js-banner-next');
	if (prev && next) {
		bannerOptions.navigation = {
		prevEl: prev,
		nextEl: next
		};
	}
	new Swiper(mainSlider, bannerOptions);
	mainSlider.dataset.sliderInitialized = 'true';
	});
	document.querySelectorAll('.js-product-slider').forEach(function (container) {
	if (container.dataset.sliderInitialized === 'true') {
		return;
	}
	const root = container.closest('[data-slider-root]');
	const options = {
		slidesPerView: 1.9,
		spaceBetween: 8,
		breakpoints: {
		420: { slidesPerView: 2.2, spaceBetween: 8 },
		640: { slidesPerView: 3, spaceBetween: 20 },
		1024: { slidesPerView: 4, spaceBetween: 24 },
		1280: { slidesPerView: 5, spaceBetween: 28 }
		}
	};
	if (root) {
		const prev = root.querySelector('.js-slider-prev');
		const next = root.querySelector('.js-slider-next');
		if (prev && next) {
		options.navigation = {
			prevEl: prev,
			nextEl: next
		};
		}
	}
	new Swiper(container, options);
	container.dataset.sliderInitialized = 'true';
	
	});
}

function initProductGallery() {
	if (!window.Swiper) {
	return;
	}
	document.querySelectorAll('[data-gallery-root]').forEach(function (root) {
	const gallery = root.querySelector('.js-product-gallery');
	if (!gallery || gallery.dataset.sliderInitialized === 'true') {
		return;
	}
	const slidesCount = gallery.querySelectorAll('.swiper-slide').length;
	const prev = root.querySelector('.js-gallery-prev');
	const next = root.querySelector('.js-gallery-next');
	const thumbsEl = root.querySelector('.js-product-gallery-thumbs');
	let thumbsSwiper = null;
	if (thumbsEl && slidesCount > 1) {
		const orientation = thumbsEl.dataset.orientation || 'horizontal';
		const isVertical = orientation === 'vertical';
		const thumbsOptions = {
		slidesPerView: isVertical ? Math.min(slidesCount, 5) : 4.2,
		spaceBetween: isVertical ? 10 : 8,
		freeMode: true,
		watchSlidesProgress: true,
		direction: isVertical ? 'vertical' : 'horizontal',
		};
		if (isVertical) {
		thumbsOptions.mousewheel = true;
		thumbsOptions.breakpoints = {
			768: { slidesPerView: Math.min(slidesCount, 5), spaceBetween: 10 },
			1024: { slidesPerView: Math.min(slidesCount, 6), spaceBetween: 12 },
		};
		} else {
		thumbsOptions.breakpoints = {
			640: { slidesPerView: 5, spaceBetween: 10 },
			1024: { slidesPerView: 6, spaceBetween: 12 },
		};
		}
		thumbsSwiper = new Swiper(thumbsEl, thumbsOptions);
		thumbsEl.dataset.sliderInitialized = 'true';
	}
	const options = {
		slidesPerView: 1,
		spaceBetween: 12,
		loop: slidesCount > 1,
		speed: 600,
	};
	if (thumbsSwiper) {
		options.thumbs = { swiper: thumbsSwiper };
	}
	if (prev && next && slidesCount > 1) {
		options.navigation = {
		prevEl: prev,
		nextEl: next,
		};
		prev.classList.remove('hidden');
		next.classList.remove('hidden');
	}
	new Swiper(gallery, options);
	gallery.dataset.sliderInitialized = 'true';
	});
}

document.addEventListener('DOMContentLoaded', function () {
	initProductSliders();
	initProductGallery();
});
document.body.addEventListener('htmx:afterSwap', function (event) {
	lucide.createIcons();
	
	if (event.detail.target && event.detail.target.closest('#page')) {
	initProductSliders();
	initProductGallery();
	lucide.createIcons();
	}
});