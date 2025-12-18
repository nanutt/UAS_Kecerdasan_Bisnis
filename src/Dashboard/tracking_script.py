def inject_tracking_script(api_base_url="http://localhost:5000"):
    """Inject JavaScript untuk tracking user interaction"""
    tracking_js = """
    <script>
    // Generate session ID
    let sessionId = sessionStorage.getItem('session_id');
    if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('session_id', sessionId);
    }
    
    let sessionStart = Date.now();
    let clickCount = 0;
    let errorCount = 0;
    let lastElement = null;
    
    // Track page load
    window.addEventListener('load', function() {
        trackEvent('page_load', 'page', 'dashboard_main', true);
    });
    
    // Track page exit & save session
    window.addEventListener('beforeunload', function() {
        let sessionDuration = Math.floor((Date.now() - sessionStart) / 1000);
        let isBounceSess = sessionDuration < 30 && clickCount < 3;
        
        saveSession(sessionDuration, clickCount, errorCount, isBounceSess);
        trackEvent('page_exit', 'page', 'dashboard_main', true);
    });
    
    // Track clicks
    document.addEventListener('click', function(e) {
        clickCount++;
        let elementName = getElementName(e.target);
        trackEvent('click', e.target.tagName.toLowerCase(), elementName, true);
        lastElement = elementName;
    });
    
    // Track Streamlit widget changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes') {
                let element = mutation.target;
                let elementName = getElementName(element);
                if (elementName !== 'unknown') {
                    trackEvent('widget_change', 'streamlit_widget', elementName, true);
                }
            }
        });
    });
    
    observer.observe(document.body, {
        attributes: true,
        subtree: true,
        attributeFilter: ['aria-selected', 'aria-checked', 'value']
    });
    
    // Function to identify element
    function getElementName(element) {
        // Radio button tahun
        if (element.closest('[data-testid="stRadio"]')) {
            return 'radio_year';
        }
        
        // Selectbox
        let selectbox = element.closest('[data-testid="stSelectbox"]');
        if (selectbox) {
            let label = selectbox.textContent || '';
            if (label.includes('Wilayah') || label.includes('wilayah')) return 'dropdown_wilayah';
            if (label.includes('Kategori') || label.includes('kategori')) return 'dropdown_kategori';
            return 'dropdown_unknown';
        }
        
        // Plotly charts
        if (element.closest('.plotly-graph-div')) {
            let container = element.closest('[style*="background"]');
            if (!container) return 'chart_unknown';
            
            let html = container.innerHTML;
            if (html.includes('Grafik Tren')) return 'chart_trend';
            if (html.includes('Donut') || html.includes('donut')) return 'chart_donut';
            if (html.includes('Kasus Penyakit')) return 'chart_stacked_bar_cases';
            if (html.includes('Tenaga Kesehatan') && html.includes('Tahun')) return 'chart_stacked_bar_workforce';
            if (html.includes('Korelasi')) return 'chart_scatter_correlation';
            if (html.includes('Kategori')) return 'chart_pie_kategori';
            return 'chart_unknown';
        }
        
        // Map
        if (element.closest('.folium-map') || element.closest('[class*="leaflet"]')) {
            return 'map_wilayah';
        }
        
        // Cards
        if (element.closest('[style*="linear-gradient"]')) {
            let html = element.closest('[style*="linear-gradient"]').innerHTML;
            if (html.includes('Total Kasus')) return 'card_summary';
            if (html.includes('Status Beban')) return 'card_workload';
        }
        
        // Table
        if (element.closest('table') || element.closest('[style*="table"]')) {
            return 'table_gap_analysis';
        }
        
        return element.id || element.className || 'unknown';
    }
    
    // Track event function
    function trackEvent(actionName, elementType, elementName, isSuccess, errorMsg = null) {
        let eventData = {
            session_id: sessionId,
            action_name: actionName,
            element_type: elementType,
            element_name: elementName,
            timestamp: new Date().toISOString(),
            is_success: isSuccess ? 1 : 0,
            error_message: errorMsg,
            page_url: window.location.href,
            device_type: /Mobile|Android|iPhone/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            browser: navigator.userAgent.split(' ').pop().split('/')[0],
            screen_resolution: window.screen.width + 'x' + window.screen.height,
            previous_element: lastElement
        };
        
        // Send to backend API
        fetch('{api_base_url}/api/track', {{
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(eventData),
            keepalive: true
        }).catch(err => {
            console.error('Tracking error:', err);
            errorCount++;
        });
        
        // Backup to localStorage
        let logs = JSON.parse(localStorage.getItem('user_logs') || '[]');
        logs.push(eventData);
        if (logs.length > 100) logs = logs.slice(-100);
        localStorage.setItem('user_logs', JSON.stringify(logs));
    }
    
    // Save session data
    function saveSession(duration, clicks, errors, isBounce) {
        let sessionData = {
            session_id: sessionId,
            session_start: new Date(sessionStart).toISOString(),
            session_end: new Date().toISOString(),
            total_duration_sec: duration,
            total_clicks: clicks,
            total_errors: errors,
            is_bounce: isBounce ? 1 : 0
        };
        
        fetch('{api_base_url}/api/session', {{
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(sessionData),
            keepalive: true
        }).catch(err => console.error('Session save error:', err));
    }
    
    // Track errors
    window.addEventListener('error', function(e) {
        errorCount++;
        trackEvent('error', 'javascript', 'page_error', false, e.message);
    });
    
    console.log('✅ User tracking initialized. Session ID:', sessionId);
    </script>
    """
    return tracking_js