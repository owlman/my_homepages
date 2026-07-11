(function () {
	"use strict";

	var html = document.documentElement;
	var STORAGE_KEY = "owlman-theme";

	function getPreferredTheme() {
		var stored = localStorage.getItem(STORAGE_KEY);
		if (stored === "light" || stored === "dark") {
			return stored;
		}
		return "dark";
	}

	function applyTheme(theme) {
		html.setAttribute("data-bs-theme", theme);
	}

	applyTheme(getPreferredTheme());

	document.addEventListener("DOMContentLoaded", function () {
		var toggle = document.getElementById("themeToggle");
		if (toggle) {
			toggle.addEventListener("click", function () {
				var next =
					html.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
				applyTheme(next);
				localStorage.setItem(STORAGE_KEY, next);
			});
		}

		var year = document.getElementById("year");
		if (year) {
			year.textContent = new Date().getFullYear();
		}

		loadBooks();
		loadPosts();
		initReveal();
		initBackToTop();
		initReadingProgress();
		initTabHash();
	});

	function escapeHtml(s) {
		return String(s).replace(/[&<>"']/g, function (c) {
			return {
				"&": "&amp;",
				"<": "&lt;",
				">": "&gt;",
				'"': "&quot;",
				"'": "&#39;",
			}[c];
		});
	}

	function renderGrid(el, list) {
		el.innerHTML = list
			.map(function (b) {
				var t = escapeHtml(b.title);
				return (
					'<div class="col">' +
					'<a class="book-thumb" target="_blank" rel="noopener noreferrer" href="' +
					escapeHtml(b.url) +
					'" title="' +
					t +
					'">' +
					'<img src="' +
					escapeHtml(b.cover) +
					'" alt="《' +
					t +
					'》封面" width="' +
					b.w +
					'" height="' +
					b.h +
					'" loading="lazy" />' +
					'<span class="book-thumb-title">' +
					t +
					"</span>" +
					"</a>" +
					"</div>"
				);
			})
			.join("");
	}

	function loadBooks() {
		var origGrid = document.getElementById("tab-original-grid");
		var transGrid = document.getElementById("tab-translation-grid");
		if (!origGrid || !transGrid) {
			return;
		}
		fetch("books.json")
			.then(function (r) {
				return r.json();
			})
			.then(function (books) {
				var orig = books.filter(function (b) {
					return b.type === "original";
				});
				var trans = books.filter(function (b) {
					return b.type === "translation";
				});
				renderGrid(origGrid, orig);
				renderGrid(transGrid, trans);
				var ob = document.getElementById("count-original");
				var tb = document.getElementById("count-translation");
				if (ob) ob.textContent = orig.length;
				if (tb) tb.textContent = trans.length;
			})
			.catch(function (err) {
				console.error("加载 books.json 失败:", err);
			});
	}

	function loadPosts() {
		var grid = document.getElementById("posts-grid");
		if (!grid) {
			return;
		}
		fetch("posts.json")
			.then(function (r) {
				return r.json();
			})
			.then(function (posts) {
				grid.innerHTML = posts
					.map(function (p) {
						var t = escapeHtml(p.title);
						var d = p.date || "";
						return (
							'<div class="col">' +
							'<a class="post-card" target="_blank" rel="noopener noreferrer" href="' +
							escapeHtml(p.url) +
							'">' +
							'<h3 class="post-card-title">' +
							t +
							"</h3>" +
							(d ? '<span class="post-card-date">' + d + "</span>" : "") +
							'<span class="post-card-more">阅读全文 →</span>' +
							"</a>" +
							"</div>"
						);
					})
					.join("");
			})
			.catch(function (err) {
				console.error("加载 posts.json 失败:", err);
			});
	}

	function initReveal() {
		var els = document.querySelectorAll(".reveal");
		if (!("IntersectionObserver" in window) || els.length === 0) {
			els.forEach(function (el) {
				el.classList.add("is-visible");
			});
			return;
		}
		var io = new IntersectionObserver(
			function (entries, obs) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add("is-visible");
						obs.unobserve(entry.target);
					}
				});
			},
			{ threshold: 0.1 }
		);
		els.forEach(function (el) {
			io.observe(el);
		});
	}

	function initBackToTop() {
		var btn = document.getElementById("backToTop");
		if (!btn) {
			return;
		}
		window.addEventListener("scroll", function () {
			if (window.scrollY > 400) {
				btn.classList.add("show");
			} else {
				btn.classList.remove("show");
			}
		});
		btn.addEventListener("click", function () {
			window.scrollTo({ top: 0, behavior: "smooth" });
		});
	}

	function initReadingProgress() {
		var bar = document.getElementById("readingProgress");
		if (!bar) {
			return;
		}
		window.addEventListener("scroll", function () {
			var scrollTop = window.scrollY;
			var docHeight = document.documentElement.scrollHeight - window.innerHeight;
			if (docHeight > 0) {
				bar.style.width = (scrollTop / docHeight) * 100 + "%";
			}
		});
	}

	function initTabHash() {
		var tabs = document.getElementById("worksTab");
		if (!tabs) {
			return;
		}
		function switchFromHash() {
			var hash = location.hash;
			if (hash === "#works-original") {
				var btn = document.getElementById("tab-original-btn");
				if (btn) {
					bootstrap.Tab.getOrCreateInstance(btn).show();
				}
			} else if (hash === "#works-translation") {
				var btn = document.getElementById("tab-translation-btn");
				if (btn) {
					bootstrap.Tab.getOrCreateInstance(btn).show();
				}
			}
		}
		switchFromHash();
		window.addEventListener("hashchange", switchFromHash);
	}

})();
