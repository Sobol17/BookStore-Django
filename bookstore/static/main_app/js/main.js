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

window.rangeSlider = function (config) {
	const initial = config || {};
	const toNumber = function (value, fallback) {
		const parsed = Number(value);
		return Number.isFinite(parsed) ? parsed : fallback;
	};
	return {
		min: toNumber(initial.min, 0),
		max: toNumber(initial.max, 100),
		from: toNumber(initial.from, 20),
		to: toNumber(initial.to, 80),
		step: Math.max(1, toNumber(initial.step, 1)),
		dragFrom: false,
		dragTo: false,
		formatter: new Intl.NumberFormat('ru-RU'),
		init($refs) {
			const refs = $refs || this.$refs || {};
			const sliderRef = refs.slider;
			if (!sliderRef) {
				console.warn('Range slider: missing $refs.slider reference');
				return;
			}
			this.sliderEl = sliderRef;
			this.normalize();
		},
		normalize() {
			this.range = Math.max(this.max - this.min, 1);
			this.from = this.clamp(this.from);
			this.to = this.clamp(this.to);
		},
		startDrag(handle, event) {
			if (handle === 'from') {
				this.dragFrom = true;
				this.dragTo = false;
			} else {
				this.dragTo = true;
				this.dragFrom = false;
			}
			if (event) {
				this.drag(event);
			}
		},
		drag(event) {
			if (!this.dragFrom && !this.dragTo) {
				return;
			}
			if (event && event.cancelable) {
				event.preventDefault();
			}
			const clientX = event.touches && event.touches.length ? event.touches[0].clientX : event.clientX;
			const rect = this.sliderEl.getBoundingClientRect();
			const ratio = (clientX - rect.left) / rect.width;
			let value = this.min + ratio * (this.max - this.min);
			value = this.snap(this.clamp(value));
			if (this.dragFrom) {
				this.from = value;
			} else if (this.dragTo) {
				this.to = value;
			}
		},
		dragEnd() {
			this.dragFrom = false;
			this.dragTo = false;
		},
		valueToPercent(value) {
			return ((value - this.min) / (this.max - this.min || 1)) * 100;
		},
		getFromPos() {
			return `${Math.min(100, Math.max(0, this.valueToPercent(this.from)))}%`;
		},
		getToPos() {
			return `${Math.min(100, Math.max(0, this.valueToPercent(this.to)))}%`;
		},
		getMinPos() {
			const minPercent = Math.min(this.valueToPercent(this.from), this.valueToPercent(this.to));
			return `${Math.min(100, Math.max(0, minPercent))}%`;
		},
		getWidth() {
			const minPercent = Math.min(this.valueToPercent(this.from), this.valueToPercent(this.to));
			const maxPercent = Math.max(this.valueToPercent(this.from), this.valueToPercent(this.to));
			return `${Math.max(0, maxPercent - minPercent)}%`;
		},
		getLowerValue() {
			return Math.min(this.from, this.to);
		},
		getUpperValue() {
			return Math.max(this.from, this.to);
		},
		handleKey(event, handle) {
			const key = event.key;
			const decrementKeys = ['ArrowLeft', 'ArrowDown'];
			const incrementKeys = ['ArrowRight', 'ArrowUp'];
			let delta = 0;
			if (decrementKeys.includes(key)) {
				delta = -this.step;
			} else if (incrementKeys.includes(key)) {
				delta = this.step;
			} else if (key === 'Home') {
				this.setHandleValue(handle, this.min);
				event.preventDefault();
				return;
			} else if (key === 'End') {
				this.setHandleValue(handle, this.max);
				event.preventDefault();
				return;
			} else {
				return;
			}
			event.preventDefault();
			this.setHandleValue(handle, (handle === 'from' ? this.from : this.to) + delta);
		},
		setHandleValue(handle, value) {
			const snapped = this.snap(this.clamp(value));
			if (handle === 'from') {
				this.from = snapped;
			} else {
				this.to = snapped;
			}
		},
		clamp(value) {
			if (Number.isNaN(value)) {
				return this.min;
			}
			return Math.min(this.max, Math.max(this.min, value));
		},
		snap(value) {
			const stepsFromMin = Math.round((value - this.min) / this.step);
			return this.min + stepsFromMin * this.step;
		},
		formatValue(value) {
			return this.formatter.format(value);
		}
	};
};

if (window.Alpine && typeof window.Alpine.data === 'function') {
	window.Alpine.data('rangeSlider', window.rangeSlider);
}
document.addEventListener('alpine:init', function () {
	if (window.Alpine && typeof window.Alpine.data === 'function') {
		window.Alpine.data('rangeSlider', window.rangeSlider);
	}
});

window.authorAutocomplete = function (initialValue, endpoint) {
	const normalizeValue = function (value) {
		return typeof value === 'string' ? value : '';
	};
	return {
		value: normalizeValue(initialValue),
		endpoint,
		open: false,
		suggestions: [],
		highlightedIndex: -1,
		debounceTimer: null,
		abortController: null,
		minChars: 1,
		openPanel() {
			this.open = true;
		},
		closePanel() {
			this.open = false;
			this.highlightedIndex = -1;
			this.cancelPending();
		},
		handleInput() {
			this.open = true;
			if (!this.value || this.value.length < this.minChars) {
				this.suggestions = [];
				this.highlightedIndex = -1;
				this.cancelPending(true);
				return;
			}
			this.scheduleFetch();
		},
		scheduleFetch() {
			this.cancelPending();
			this.debounceTimer = setTimeout(() => {
				this.fetchSuggestions();
			}, 200);
		},
		cancelPending(skipAbort) {
			if (this.debounceTimer) {
				clearTimeout(this.debounceTimer);
				this.debounceTimer = null;
			}
			if (!skipAbort && this.abortController) {
				this.abortController.abort();
				this.abortController = null;
			}
		},
		async fetchSuggestions() {
			if (!this.endpoint) {
				return;
			}
			this.abortController = new AbortController();
			const params = new URLSearchParams();
			if (this.value) {
				params.set('q', this.value);
			}
			try {
				const response = await fetch(`${this.endpoint}?${params.toString()}`, {
					signal: this.abortController.signal,
					headers: {
						Accept: 'application/json'
					}
				});
				if (response.ok) {
					const data = await response.json();
					this.suggestions = Array.isArray(data.results) ? data.results : [];
					this.highlightedIndex = this.suggestions.length ? 0 : -1;
				}
			} catch (error) {
				if (error.name !== 'AbortError') {
					console.error('Author autocomplete error', error);
				}
			} finally {
				this.abortController = null;
			}
		},
		moveHighlight(step) {
			if (!this.suggestions.length) {
				this.highlightedIndex = -1;
				return;
			}
			if (this.highlightedIndex === -1) {
				this.highlightedIndex = 0;
				return;
			}
			const nextIndex = (this.highlightedIndex + step + this.suggestions.length) % this.suggestions.length;
			this.highlightedIndex = nextIndex;
		},
		select(value) {
			this.value = value;
			this.closePanel();
		},
		selectHighlighted() {
			if (this.highlightedIndex >= 0 && this.highlightedIndex < this.suggestions.length) {
				this.select(this.suggestions[this.highlightedIndex]);
			} else {
				this.closePanel();
			}
		}
	};
};

if (window.Alpine && typeof window.Alpine.data === 'function') {
	window.Alpine.data('authorAutocomplete', window.authorAutocomplete);
}
document.addEventListener('alpine:init', function () {
	if (window.Alpine && typeof window.Alpine.data === 'function') {
		window.Alpine.data('authorAutocomplete', window.authorAutocomplete);
	}
});

window.reviewRating = function (config) {
	const initial = Number(config && config.initial) || 5;
	return {
		ratingValue: initial,
		setRating(value) {
			this.ratingValue = value;
		}
	};
};

if (window.Alpine && typeof window.Alpine.data === 'function') {
	window.Alpine.data('reviewRating', window.reviewRating);
}
document.addEventListener('alpine:init', function () {
	if (window.Alpine && typeof window.Alpine.data === 'function') {
		window.Alpine.data('reviewRating', window.reviewRating);
	}
});

document.body.addEventListener('close-review-modal', function () {
	const modalRoot = document.getElementById('modal-root');
	if (modalRoot) {
		modalRoot.innerHTML = '';
	}
});

document.addEventListener('DOMContentLoaded', function () {
	initProductSliders();
	initProductGallery();
});
document.body.addEventListener('htmx:afterSwap', function (event) {
	lucide.createIcons();
	if (event.detail && event.detail.target && window.Alpine) {
		window.Alpine.initTree(event.detail.target);
	}
	
	if (event.detail.target && event.detail.target.closest('#page')) {
		initProductSliders();
		initProductGallery();
		lucide.createIcons();
	}
});
