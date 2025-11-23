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

if (typeof window.getCookie !== 'function') {
	window.getCookie = function (name) {
		let cookieValue = null;
		if (document.cookie && document.cookie !== '') {
			const cookies = document.cookie.split(';');
			for (let i = 0; i < cookies.length; i += 1) {
				const cookie = cookies[i].trim();
				if (cookie.substring(0, name.length + 1) === `${name}=`) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	};
}

if (typeof window.showNotification !== 'function') {
	window.showNotification = function (message) {
		const notification = document.createElement('div');
		notification.className = 'fixed top-20 right-4 bg-black text-white px-6 py-3 rounded shadow-lg z-50 transform translate-x-full transition-transform duration-300';
		notification.textContent = message;
		document.body.appendChild(notification);
		setTimeout(() => {
			notification.style.transform = 'translateX(0)';
		}, 10);
		setTimeout(() => {
			notification.style.transform = 'translateX(100%)';
			setTimeout(() => {
				notification.remove();
			}, 300);
		}, 3000);
	};
}

function getProductCardElements(productId) {
	const nodes = document.querySelectorAll(`[data-product-card="${productId}"]`);
	return Array.from(nodes).map((node) => ({
		element: node,
		addWrapper: node.querySelector('[data-card-add]'),
		qtyWrapper: node.querySelector('[data-card-qty]'),
		qtyValue: node.querySelector('[data-card-qty-value]'),
		addUrl: node.dataset.addUrl,
		updateUrlTemplate: node.dataset.updateUrlTemplate,
		productName: node.dataset.productName || '',
	}));
}

function showProductCardQuantity(cards, cartItemId, quantity) {
	cards.forEach((card) => {
		if (!card.qtyWrapper || !card.qtyValue) {
			return;
		}
		card.qtyWrapper.classList.remove('hidden');
		card.qtyWrapper.dataset.cartItemId = cartItemId;
		card.qtyValue.textContent = quantity;
		if (card.addWrapper) {
			card.addWrapper.classList.add('hidden');
		}
	});
}

function resetProductCardState(cards) {
	cards.forEach((card) => {
		if (card.qtyWrapper) {
			card.qtyWrapper.classList.add('hidden');
			card.qtyWrapper.dataset.cartItemId = '';
		}
		if (card.addWrapper) {
			card.addWrapper.classList.remove('hidden');
		}
	});
}

function refreshCartModal() {
	if (typeof openCart === 'function') {
		openCart();
	}
}

window.showCartModal = function showCartModal() {
	const overlay = document.getElementById('cart-overlay');
	const modal = document.getElementById('cart-modal');
	if (!overlay || !modal) {
		return;
	}
	overlay.classList.remove('closed');
	overlay.classList.add('open');
	modal.classList.remove('closed');
	modal.classList.add('open');
	document.body.style.overflow = 'hidden';
};

window.hideCartModal = function hideCartModal() {
	const overlay = document.getElementById('cart-overlay');
	const modal = document.getElementById('cart-modal');
	if (!overlay || !modal) {
		return;
	}
	overlay.classList.remove('open');
	overlay.classList.add('closed');
	modal.classList.remove('open');
	modal.classList.add('closed');
	setTimeout(() => {
		const container = document.getElementById('cart-container');
		if (container) {
			container.innerHTML = '';
		}
		document.body.style.overflow = '';
	}, 300);
};

function updateProductCardQuantity(productId, newQuantity) {
	const cards = getProductCardElements(productId);
	if (!cards.length) {
		return;
	}
	const qtyWrapper = cards[0].qtyWrapper;
	if (!qtyWrapper) {
		return;
	}
	const cartItemId = qtyWrapper.dataset.cartItemId;
	const template = cards[0].updateUrlTemplate;
	if (!cartItemId || !template) {
		return;
	}
	const targetQuantity = Math.max(0, newQuantity);
	const url = template.replace('/0/', `/${cartItemId}/`);
	const formData = new FormData();
	formData.append('quantity', targetQuantity);
	fetch(url, {
		method: 'POST',
		body: formData,
		headers: {
			'X-CSRFToken': window.getCookie('csrftoken'),
		},
	})
		.then((response) => response.json())
		.then((data) => {
			if (data.error) {
				window.showNotification(data.error);
				return;
			}
			if (typeof updateHeaderCartCount === 'function') {
				updateHeaderCartCount(data.total_items);
			}
			if (data.removed || data.quantity <= 0) {
				resetProductCardState(cards);
				window.showNotification('Товар удалён из корзины');
			} else {
				showProductCardQuantity(cards, data.cart_item_id || cartItemId, data.quantity);
				window.showNotification('Количество обновлено');
			}
		})
		.catch((error) => {
			console.error('Error updating cart item', error);
			window.showNotification('Не удалось обновить корзину');
		});
}

window.addProductCardToCart = function addProductCardToCart(productId) {
	const cards = getProductCardElements(productId);
	if (!cards.length) {
		return;
	}
	const addUrl = cards[0].addUrl;
	if (!addUrl) {
		return;
	}
	const formData = new FormData();
	formData.append('quantity', '1');
	fetch(addUrl, {
		method: 'POST',
		body: formData,
		headers: {
			'X-CSRFToken': window.getCookie('csrftoken'),
		},
	})
		.then((response) => response.json())
		.then((data) => {
			if (data.error) {
				window.showNotification(data.error);
				return;
			}
			if (typeof updateHeaderCartCount === 'function') {
				updateHeaderCartCount(data.total_items);
			}
			showProductCardQuantity(cards, data.cart_item_id, data.quantity || 1);
			window.showNotification(data.message || 'Товар добавлен в корзину');
			refreshCartModal();
		})
		.catch((error) => {
			console.error('Error adding to cart', error);
			window.showNotification('Не удалось добавить товар в корзину');
		});
};

window.changeProductCardQuantity = function changeProductCardQuantity(productId, delta) {
	const cards = getProductCardElements(productId);
	if (!cards.length) {
		return;
	}
	const qtyValue = cards[0].qtyValue;
	if (!qtyValue) {
		return;
	}
	const currentQuantity = parseInt(qtyValue.textContent, 10) || 0;
	const nextQuantity = currentQuantity + delta;
	updateProductCardQuantity(productId, nextQuantity);
};

document.body.addEventListener('click', function (event) {
	const addButton = event.target.closest('[data-card-add-button]');
	if (addButton) {
		const card = addButton.closest('[data-product-card]');
		const productId = card ? card.dataset.productCard : null;
		if (productId) {
			addProductCardToCart(productId);
		}
		return;
	}
	const qtyButton = event.target.closest('[data-card-qty-button]');
	if (qtyButton) {
		const card = qtyButton.closest('[data-product-card]');
		const productId = card ? card.dataset.productCard : null;
		const delta = Number(qtyButton.dataset.delta || 0);
		if (productId && delta) {
			changeProductCardQuantity(productId, delta);
		}
	}
});

document.body.addEventListener('cart-updated', function (event) {
	const detail = event.detail || {};
	if (typeof detail.total_items !== 'undefined' && typeof window.updateHeaderCartCount === 'function') {
		window.updateHeaderCartCount(detail.total_items);
	}
	const productId = detail.product_id ? String(detail.product_id) : null;
	const quantity = typeof detail.quantity !== 'undefined' ? Number(detail.quantity) : null;
	if (productId) {
		const cards = getProductCardElements(productId);
		if (cards.length) {
			if (quantity && quantity > 0) {
				showProductCardQuantity(cards, detail.cart_item_id || '', quantity);
			} else {
				resetProductCardState(cards);
			}
		}
	}
	if (detail.message) {
		window.showNotification(detail.message);
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
	const swapTarget = event.detail && event.detail.target ? event.detail.target : null;
	if (swapTarget && swapTarget.id === 'cart-container') {
		const overlay = swapTarget.querySelector('#cart-overlay');
		if (overlay && typeof window.updateHeaderCartCount === 'function' && overlay.dataset.cartTotal) {
			window.updateHeaderCartCount(Number(overlay.dataset.cartTotal));
		}
		if (typeof window.showCartModal === 'function') {
			window.showCartModal();
		}
	}
});
