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
		renderSocial();
		initReveal();
		initBackToTop();
		initReadingProgress();
		initTabs();
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
				var yearBadge = b.year ? '<span class="book-year">' + b.year + "</span>" : "";
				return (
					'<div class="col">' +
					'<a class="book-thumb" target="_blank" rel="noopener noreferrer" href="' +
					escapeHtml(b.url) +
					'" title="' +
					t +
					'">' +
					'<span class="book-thumb-wrap">' +
					'<img src="' +
					escapeHtml(b.cover) +
					'" alt="《' +
					t +
					'》封面" width="' +
					b.w +
					'" height="' +
					b.h +
					'" loading="lazy" />' +
					yearBadge +
					"</span>" +
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
				updateJsonLd(books);
			})
			.catch(function (err) {
				console.error("加载 books.json 失败:", err);
			});
	}

	function updateJsonLd(books) {
		var script = document.querySelector('script[type="application/ld+json"]');
		if (!script) return;
		try {
			var data = JSON.parse(script.textContent);
			var graph = data["@graph"];
			if (!Array.isArray(graph)) return;
			var nonBook = graph.filter(function (item) {
				return item["@type"] !== "Book";
			});
			var bookEntries = books.map(function (b) {
				var entry = {
					"@type": "Book",
					"name": b.title,
					"url": b.url,
					"inLanguage": "zh-CN"
				};
				if (b.type === "original") {
					entry.author = { "@id": "https://www.owlman.cn/#owlman" };
				} else {
					entry.translator = { "@id": "https://www.owlman.cn/#owlman" };
				}
				return entry;
			});
			data["@graph"] = nonBook.concat(bookEntries);
			script.textContent = JSON.stringify(data);
		} catch (e) {
			/* 静默降级——HTML 中的静态 JSON-LD 作为后备 */
		}
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
						var s = p.summary
							? '<p class="post-card-summary">' + escapeHtml(p.summary) + "</p>"
							: "";
						return (
							'<div class="col">' +
							'<a class="post-card" target="_blank" rel="noopener noreferrer" href="' +
							escapeHtml(p.url) +
							'">' +
							'<h3 class="post-card-title">' +
							t +
							"</h3>" +
							(d ? '<span class="post-card-date">' + d + "</span>" : "") +
							s +
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

	function renderSocial() {
		var containers = [
			document.getElementById("hero-social"),
			document.getElementById("contact-social"),
		].filter(Boolean);
		if (containers.length === 0) {
			return;
		}
		fetch("data/social-links.json")
			.then(function (r) {
				return r.json();
			})
			.then(function (links) {
				var html = links
					.map(function (l) {
						var attrs = 'aria-label="' + escapeHtml(l.label) + '"';
						if (l.external) {
							attrs += ' target="_blank" rel="noopener noreferrer"';
						}
						return (
							'<li><a href="' +
							escapeHtml(l.href) +
							'" ' +
							attrs +
							">" +
							'<svg class="brand-icon" aria-hidden="true"><use href="#' +
							escapeHtml(l.id) +
							'" /></svg>' +
							"</a></li>"
						);
					})
					.join("");
				containers.forEach(function (el) {
					el.innerHTML = html;
				});
			})
			.catch(function (err) {
				console.error("加载 social-links.json 失败:", err);
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

	function initTabs() {
		var tabBar = document.getElementById("worksTab");
		if (!tabBar) {
			return;
		}
		var buttons = tabBar.querySelectorAll("[data-tab-target]");
		if (buttons.length === 0) {
			return;
		}

		function activate(target) {
			buttons.forEach(function (btn) {
				var isActive = btn.dataset.tabTarget === target;
				btn.classList.toggle("active", isActive);
				btn.setAttribute("aria-selected", isActive ? "true" : "false");
				var panel = document.querySelector(btn.dataset.tabTarget);
				if (panel) {
					panel.classList.toggle("show", isActive);
					panel.classList.toggle("active", isActive);
				}
			});
		}

		buttons.forEach(function (btn) {
			btn.addEventListener("click", function () {
				activate(btn.dataset.tabTarget);
				var slug = btn.dataset.tabTarget
					.replace(/^#tab-/, "")
					.replace(/-tab$/, "");
				var newHash = "#works-" + slug;
				if (history.replaceState) {
					history.replaceState(null, "", newHash);
				}
			});
		});

		window.addEventListener("hashchange", function () {
			if (location.hash === "#works-translation") {
				activate("#tab-translation");
			} else if (location.hash === "#works-original") {
				activate("#tab-original");
			}
		});

		if (location.hash === "#works-translation") {
			activate("#tab-translation");
		} else {
			activate("#tab-original");
		}
	}

})();
