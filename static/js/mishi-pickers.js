(function () {
    'use strict';

    var MESES = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];
    var MESES_CORTO = [
        'ene', 'feb', 'mar', 'abr', 'may', 'jun',
        'jul', 'ago', 'sep', 'oct', 'nov', 'dic'
    ];
    var DIAS_SEMANA = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do'];

    var CHEV_SVG =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="m6 9 6 6 6-6"/></svg>';

    var CHECK_SVG =
        '<svg class="m-select-check" width="15" height="15" viewBox="0 0 24 24" fill="none" ' +
        'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M20 6 9 17l-5-5"/></svg>';

    var CAL_SVG =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<rect x="3" y="4" width="18" height="18" rx="3.5"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>';

    var PREV_SVG =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="m15 18-6-6 6-6"/></svg>';

    var NEXT_SVG =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="m9 18 6-6-6-6"/></svg>';

    var activePicker = null;

    function pad2(n) {
        return n < 10 ? '0' + n : String(n);
    }

    function toIso(d) {
        return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
    }

    function parseIso(str) {
        if (!str || !/^\d{4}-\d{2}-\d{2}$/.test(str)) return null;
        var p = str.split('-');
        var y = Number(p[0]);
        var m = Number(p[1]) - 1;
        var day = Number(p[2]);
        var d = new Date(y, m, day);
        if (d.getFullYear() !== y || d.getMonth() !== m || d.getDate() !== day) return null;
        return d;
    }

    function formatDisplayDate(isoStr) {
        var d = parseIso(isoStr);
        if (!d) return '';
        return d.getDate() + ' ' + MESES_CORTO[d.getMonth()] + ' ' + d.getFullYear();
    }

    function todayLocal() {
        var now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }

    function closeActive(restoreFocus) {
        if (!activePicker) return;
        var current = activePicker;
        activePicker = null;
        current.close(Boolean(restoreFocus));
    }

    function positionPopover(trigger, popover, matchWidth) {
        var rect = trigger.getBoundingClientRect();
        var margin = 12;
        var gap = 6;
        var vw = window.innerWidth;
        var vh = window.innerHeight;

        if (matchWidth) {
            popover.style.width = Math.max(rect.width, 180) + 'px';
        }

        // Medir en estado oculto pero renderizado
        var popW = popover.offsetWidth || (matchWidth ? rect.width : 296);
        var popH = popover.offsetHeight || 280;

        var left = rect.left;
        if (left + popW > vw - margin) {
            left = vw - popW - margin;
        }
        if (left < margin) {
            left = margin;
        }

        var spaceBelow = vh - rect.bottom - margin;
        var spaceAbove = rect.top - margin;
        var flipUp = spaceBelow < popH && spaceAbove > spaceBelow;

        var top;
        if (flipUp) {
            top = Math.max(margin, rect.top - popH - gap);
            popover.classList.add('is-flipped');
        } else {
            top = Math.min(vh - popH - margin, rect.bottom + gap);
            if (top < margin) top = margin;
            popover.classList.remove('is-flipped');
        }

        // Origen de escala alineado al trigger
        var triggerCenterX = rect.left + rect.width / 2 - left;
        var originX = Math.max(16, Math.min(popW - 16, triggerCenterX));
        popover.style.transformOrigin = Math.round(originX) + 'px ' + (flipUp ? '100%' : '0%');
        popover.style.left = Math.round(left) + 'px';
        popover.style.top = Math.round(top) + 'px';
    }

    function triggerVariantClass(el) {
        if (el.classList.contains('m-sheet-input')) return 'm-picker-trigger--sheet';
        if (el.classList.contains('app-field')) return 'm-picker-trigger--app';
        return 'm-picker-trigger--input';
    }

    function bindLabelToTrigger(nativeEl, trigger) {
        if (!nativeEl.id) return;
        var label = document.querySelector('label[for="' + nativeEl.id + '"]');
        if (!label) return;
        label.addEventListener('click', function (e) {
            e.preventDefault();
            trigger.focus();
            trigger.click();
        });
    }

    /* ======================================================================
       1. SELECT PERSONALIZADO ESTILO MISHI
       ====================================================================== */
    function enhanceSelect(selectEl) {
        if (
            !selectEl ||
            selectEl.dataset.mishiEnhanced === '1' ||
            selectEl.hasAttribute('multiple') ||
            selectEl.hasAttribute('data-native-picker') ||
            selectEl.closest('.sr-only') ||
            selectEl.closest('.mishi-select')
        ) {
            return;
        }
        selectEl.dataset.mishiEnhanced = '1';

        var wrap = document.createElement('div');
        wrap.className = 'm-picker-wrap m-select-wrap';
        selectEl.parentNode.insertBefore(wrap, selectEl);
        wrap.appendChild(selectEl);

        selectEl.classList.add('m-native-hidden');
        selectEl.setAttribute('tabindex', '-1');
        selectEl.setAttribute('aria-hidden', 'true');

        var listId = 'mishi-sel-list-' + (selectEl.id || Math.random().toString(36).slice(2, 8));
        var trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'm-picker-trigger ' + triggerVariantClass(selectEl);
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-controls', listId);
        if (selectEl.disabled) trigger.disabled = true;

        var valSpan = document.createElement('span');
        valSpan.className = 'm-picker-val';

        var icoSpan = document.createElement('span');
        icoSpan.className = 'm-picker-ico m-picker-chev';
        icoSpan.innerHTML = CHEV_SVG;

        trigger.appendChild(valSpan);
        trigger.appendChild(icoSpan);
        wrap.appendChild(trigger);

        var popover = document.createElement('div');
        popover.className = 'm-picker-popover m-select-popover';
        popover.setAttribute('aria-hidden', 'true');

        var ul = document.createElement('ul');
        ul.id = listId;
        ul.className = 'm-select-list';
        ul.setAttribute('role', 'listbox');
        popover.appendChild(ul);
        document.body.appendChild(popover);

        var focusedIdx = -1;
        var optionNodes = [];

        function syncLabel() {
            var opt = selectEl.options[selectEl.selectedIndex];
            valSpan.textContent = opt ? opt.textContent.trim() : '';
            valSpan.classList.toggle('is-placeholder', !opt || opt.value === '');
        }

        function buildOptions() {
            ul.innerHTML = '';
            optionNodes = [];
            Array.from(selectEl.options).forEach(function (opt, idx) {
                var li = document.createElement('li');
                li.className = 'm-select-opt';
                li.setAttribute('role', 'option');
                li.setAttribute('data-idx', String(idx));
                li.setAttribute('tabindex', '-1');

                var selected = idx === selectEl.selectedIndex;
                li.setAttribute('aria-selected', selected ? 'true' : 'false');
                if (selected) li.classList.add('is-selected');
                if (opt.disabled) li.classList.add('is-disabled');

                var txt = document.createElement('span');
                txt.className = 'm-select-opt-txt';
                txt.textContent = opt.textContent.trim();

                li.appendChild(txt);
                li.insertAdjacentHTML('beforeend', CHECK_SVG);

                li.addEventListener('click', function (e) {
                    e.stopPropagation();
                    if (opt.disabled) return;
                    chooseIndex(idx);
                });

                ul.appendChild(li);
                optionNodes.push(li);
            });
        }

        function setFocusIdx(nextIdx) {
            if (!optionNodes.length) return;
            var total = optionNodes.length;
            var idx = ((nextIdx % total) + total) % total;
            focusedIdx = idx;
            optionNodes.forEach(function (n, i) {
                n.classList.toggle('is-focused', i === idx);
            });
            var node = optionNodes[idx];
            if (node) {
                node.focus({ preventScroll: true });
                node.scrollIntoView({ block: 'nearest' });
            }
        }

        function chooseIndex(idx) {
            if (selectEl.selectedIndex !== idx) {
                selectEl.selectedIndex = idx;
                selectEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            syncLabel();
            closeActive(true);
        }

        var controller = {
            trigger: trigger,
            popover: popover,
            reposition: function () {
                positionPopover(trigger, popover, true);
            },
            close: function (restoreFocus) {
                popover.classList.remove('is-open');
                popover.setAttribute('aria-hidden', 'true');
                trigger.classList.remove('is-open');
                trigger.setAttribute('aria-expanded', 'false');
                if (restoreFocus) trigger.focus();
            }
        };

        function open() {
            if (trigger.disabled) return;
            if (activePicker === controller) {
                closeActive(true);
                return;
            }
            closeActive(false);
            buildOptions();
            positionPopover(trigger, popover, true);
            popover.setAttribute('aria-hidden', 'false');
            window.requestAnimationFrame(function () {
                popover.classList.add('is-open');
            });
            trigger.classList.add('is-open');
            trigger.setAttribute('aria-expanded', 'true');
            activePicker = controller;

            var selIdx = Math.max(0, selectEl.selectedIndex);
            setFocusIdx(selIdx);
        }

        trigger.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            open();
        });

        trigger.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                open();
            }
        });

        ul.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setFocusIdx(focusedIdx + 1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setFocusIdx(focusedIdx - 1);
            } else if (e.key === 'Home') {
                e.preventDefault();
                setFocusIdx(0);
            } else if (e.key === 'End') {
                e.preventDefault();
                setFocusIdx(optionNodes.length - 1);
            } else if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (focusedIdx >= 0) chooseIndex(focusedIdx);
            } else if (e.key === 'Tab') {
                closeActive(false);
            }
        });

        selectEl.addEventListener('change', syncLabel);
        bindLabelToTrigger(selectEl, trigger);
        syncLabel();
    }

    /* ======================================================================
       2. CALENDARIO PERSONALIZADO ESTILO MISHI
       ====================================================================== */
    function getRangePair(inputEl) {
        if (inputEl.id === 'fecha_inicio') {
            var endEl = document.getElementById('fecha_fin');
            return { startEl: inputEl, endEl: endEl };
        }
        if (inputEl.id === 'fecha_fin') {
            var startEl = document.getElementById('fecha_inicio');
            return { startEl: startEl, endEl: inputEl };
        }
        return null;
    }

    function enhanceDate(inputEl) {
        if (
            !inputEl ||
            inputEl.dataset.mishiEnhanced === '1' ||
            inputEl.hasAttribute('data-native-picker')
        ) {
            return;
        }
        inputEl.dataset.mishiEnhanced = '1';

        var wrap = document.createElement('div');
        wrap.className = 'm-picker-wrap m-date-wrap';
        inputEl.parentNode.insertBefore(wrap, inputEl);
        wrap.appendChild(inputEl);

        inputEl.classList.add('m-native-hidden');
        inputEl.setAttribute('tabindex', '-1');
        inputEl.setAttribute('aria-hidden', 'true');

        var popId = 'mishi-cal-' + (inputEl.id || Math.random().toString(36).slice(2, 8));
        var trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'm-picker-trigger m-date-trigger ' + triggerVariantClass(inputEl);
        trigger.setAttribute('aria-haspopup', 'dialog');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-controls', popId);
        if (inputEl.disabled) trigger.disabled = true;

        var valSpan = document.createElement('span');
        valSpan.className = 'm-picker-val';

        var icoSpan = document.createElement('span');
        icoSpan.className = 'm-picker-ico m-picker-cal-ico';
        icoSpan.innerHTML = CAL_SVG;

        trigger.appendChild(valSpan);
        trigger.appendChild(icoSpan);
        wrap.appendChild(trigger);

        var popover = document.createElement('div');
        popover.id = popId;
        popover.className = 'm-picker-popover m-cal-popover';
        popover.setAttribute('role', 'dialog');
        popover.setAttribute('aria-label', 'Selector de fecha');
        popover.setAttribute('aria-hidden', 'true');
        document.body.appendChild(popover);

        var viewYear = todayLocal().getFullYear();
        var viewMonth = todayLocal().getMonth();
        var ymMode = false;

        function syncLabel() {
            var formatted = formatDisplayDate(inputEl.value);
            if (formatted) {
                valSpan.textContent = formatted;
                valSpan.classList.remove('is-placeholder');
            } else {
                valSpan.textContent = 'dd/mm/aaaa';
                valSpan.classList.add('is-placeholder');
            }
        }

        function isOutOfBounds(iso) {
            var minVal = inputEl.getAttribute('min');
            var maxVal = inputEl.getAttribute('max');
            if (minVal && iso < minVal) return true;
            if (maxVal && iso > maxVal) return true;
            return false;
        }

        function setIsoValue(iso) {
            inputEl.value = iso;
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            inputEl.dispatchEvent(new Event('change', { bubbles: true }));
            syncLabel();
        }

        function renderCalendar() {
            var today = todayLocal();
            var todayIso = toIso(today);
            var selectedIso = inputEl.value || '';

            var pair = getRangePair(inputEl);
            var rangeStart = pair && pair.startEl ? pair.startEl.value : '';
            var rangeEnd = pair && pair.endEl ? pair.endEl.value : '';
            var hasRange = Boolean(rangeStart && rangeEnd && rangeStart <= rangeEnd);

            popover.innerHTML = '';

            // Header
            var head = document.createElement('div');
            head.className = 'm-cal-head';

            var monthBtn = document.createElement('button');
            monthBtn.type = 'button';
            monthBtn.className = 'm-cal-month-btn' + (ymMode ? ' is-active' : '');
            monthBtn.innerHTML = '<span>' + MESES[viewMonth] + ' ' + viewYear + '</span>' + CHEV_SVG;
            monthBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                ymMode = !ymMode;
                renderCalendar();
            });
            head.appendChild(monthBtn);

            var nav = document.createElement('div');
            nav.className = 'm-cal-nav';

            var prevBtn = document.createElement('button');
            prevBtn.type = 'button';
            prevBtn.className = 'm-cal-nav-btn';
            prevBtn.setAttribute('aria-label', ymMode ? 'Año anterior' : 'Mes anterior');
            prevBtn.innerHTML = PREV_SVG;
            prevBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                if (ymMode) {
                    viewYear -= 1;
                } else {
                    viewMonth -= 1;
                    if (viewMonth < 0) { viewMonth = 11; viewYear -= 1; }
                }
                renderCalendar();
            });

            var nextBtn = document.createElement('button');
            nextBtn.type = 'button';
            nextBtn.className = 'm-cal-nav-btn';
            nextBtn.setAttribute('aria-label', ymMode ? 'Año siguiente' : 'Mes siguiente');
            nextBtn.innerHTML = NEXT_SVG;
            nextBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                if (ymMode) {
                    viewYear += 1;
                } else {
                    viewMonth += 1;
                    if (viewMonth > 11) { viewMonth = 0; viewYear += 1; }
                }
                renderCalendar();
            });

            nav.appendChild(prevBtn);
            nav.appendChild(nextBtn);
            head.appendChild(nav);
            popover.appendChild(head);

            if (ymMode) {
                var ymGrid = document.createElement('div');
                ymGrid.className = 'm-cal-ym-grid';
                MESES.forEach(function (nombre, idx) {
                    var btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'm-cal-ym-opt' + (idx === viewMonth ? ' is-selected' : '');
                    btn.textContent = nombre.slice(0, 3);
                    btn.addEventListener('click', function (e) {
                        e.stopPropagation();
                        viewMonth = idx;
                        ymMode = false;
                        renderCalendar();
                    });
                    ymGrid.appendChild(btn);
                });
                popover.appendChild(ymGrid);
            } else {
                var wkRow = document.createElement('div');
                wkRow.className = 'm-cal-weekdays';
                DIAS_SEMANA.forEach(function (d) {
                    var sp = document.createElement('span');
                    sp.textContent = d;
                    wkRow.appendChild(sp);
                });
                popover.appendChild(wkRow);

                var grid = document.createElement('div');
                grid.className = 'm-cal-grid';

                var firstDay = new Date(viewYear, viewMonth, 1);
                var startOffset = (firstDay.getDay() + 6) % 7; // Lunes = 0
                var startDate = new Date(viewYear, viewMonth, 1 - startOffset);

                for (var i = 0; i < 42; i++) {
                    var cellDate = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + i);
                    var iso = toIso(cellDate);
                    var isOutside = cellDate.getMonth() !== viewMonth;
                    var isToday = iso === todayIso;
                    var isSelected = iso === selectedIso;
                    var disabled = isOutOfBounds(iso);

                    var dayBtn = document.createElement('button');
                    dayBtn.type = 'button';
                    dayBtn.className = 'm-cal-day';
                    dayBtn.textContent = String(cellDate.getDate());
                    dayBtn.setAttribute('data-iso', iso);

                    if (isOutside) dayBtn.classList.add('is-outside');
                    if (isToday) dayBtn.classList.add('is-today');
                    if (hasRange && iso > rangeStart && iso < rangeEnd) {
                        dayBtn.classList.add('is-in-range');
                    }
                    if (hasRange && (iso === rangeStart || iso === rangeEnd) && !isSelected) {
                        dayBtn.classList.add('is-range-edge');
                    }
                    if (isSelected) {
                        dayBtn.classList.add('is-selected');
                        dayBtn.setAttribute('aria-pressed', 'true');
                    }
                    if (disabled) {
                        dayBtn.disabled = true;
                    } else {
                        (function (targetIso) {
                            dayBtn.addEventListener('click', function (e) {
                                e.stopPropagation();
                                setIsoValue(targetIso);
                                closeActive(true);
                            });
                        })(iso);
                    }
                    grid.appendChild(dayBtn);
                }
                popover.appendChild(grid);
            }

            // Footer
            var foot = document.createElement('div');
            foot.className = 'm-cal-footer';

            if (!inputEl.hasAttribute('required')) {
                var clearBtn = document.createElement('button');
                clearBtn.type = 'button';
                clearBtn.className = 'm-cal-clear';
                clearBtn.textContent = 'Borrar';
                clearBtn.disabled = !inputEl.value;
                clearBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    setIsoValue('');
                    closeActive(true);
                });
                foot.appendChild(clearBtn);
            } else {
                var spacer = document.createElement('span');
                foot.appendChild(spacer);
            }

            var todayBtn = document.createElement('button');
            todayBtn.type = 'button';
            todayBtn.className = 'm-cal-today';
            todayBtn.textContent = 'Hoy';
            if (isOutOfBounds(todayIso)) {
                todayBtn.disabled = true;
            } else {
                todayBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    viewYear = today.getFullYear();
                    viewMonth = today.getMonth();
                    setIsoValue(todayIso);
                    closeActive(true);
                });
            }
            foot.appendChild(todayBtn);
            popover.appendChild(foot);
        }

        var controller = {
            trigger: trigger,
            popover: popover,
            reposition: function () {
                positionPopover(trigger, popover, false);
            },
            close: function (restoreFocus) {
                ymMode = false;
                popover.classList.remove('is-open');
                popover.setAttribute('aria-hidden', 'true');
                trigger.classList.remove('is-open');
                trigger.setAttribute('aria-expanded', 'false');
                if (restoreFocus) trigger.focus();
            }
        };

        function open() {
            if (trigger.disabled) return;
            if (activePicker === controller) {
                closeActive(true);
                return;
            }
            closeActive(false);

            var base = parseIso(inputEl.value) || todayLocal();
            viewYear = base.getFullYear();
            viewMonth = base.getMonth();
            ymMode = false;

            renderCalendar();
            positionPopover(trigger, popover, false);
            popover.setAttribute('aria-hidden', 'false');
            window.requestAnimationFrame(function () {
                popover.classList.add('is-open');
            });
            trigger.classList.add('is-open');
            trigger.setAttribute('aria-expanded', 'true');
            activePicker = controller;
        }

        trigger.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            open();
        });

        trigger.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                open();
            }
        });

        inputEl.addEventListener('change', syncLabel);
        bindLabelToTrigger(inputEl, trigger);
        syncLabel();
    }

    /* ======================================================================
       3. INICIALIZACIÓN GLOBAL Y EVENTOS DE CIERRE
       ====================================================================== */
    function initPickers(root) {
        var scope = root || document;
        scope.querySelectorAll('.app-screen select, .m-sheet-panel select').forEach(enhanceSelect);
        scope.querySelectorAll('.app-screen input[type="date"], .m-sheet-panel input[type="date"]').forEach(enhanceDate);
    }

    document.addEventListener('click', function (e) {
        if (!activePicker) return;
        if (activePicker.popover.contains(e.target) || activePicker.trigger.contains(e.target)) {
            return;
        }
        closeActive(false);
    });

    // Fase de captura para cerrar el popover antes de que Escape cierre un bottom sheet detrás
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && activePicker) {
            e.preventDefault();
            e.stopImmediatePropagation();
            closeActive(true);
        }
    }, true);

    window.addEventListener('resize', function () {
        if (activePicker) activePicker.reposition();
    });

    window.addEventListener('scroll', function (e) {
        if (!activePicker) return;
        if (activePicker.popover.contains(e.target)) return;
        closeActive(false);
    }, true);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { initPickers(document); });
    } else {
        initPickers(document);
    }

    window.MishiPickers = {
        init: initPickers,
        close: function () { closeActive(false); }
    };
})();
