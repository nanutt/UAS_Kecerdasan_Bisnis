def inject_tracking_script():
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
    
    // KONFIGURASI API: Gunakan hostname saat ini agar bisa diakses dari device lain
    const API_BASE_URL = "http://" + window.location.hostname + ":5000";

    // Track page load
    window.addEventListener('load', function() {
        trackEvent('page_load', 'page', 'dashboard_main', true);
    });
    
    // Track page exit & save session
    window.addEventListener('beforeunload', function() {
        let sessionDuration = Math.floor((Date.now() - sessionStart) / 1000);
        let isBounceSess = sessionDuration < 30 && clickCount < 3;
        saveSession(sessionDuration, clickCount, errorCount, isBounceSess);
    });
    
    // Track clicks
    document.addEventListener('click', function(e) {
        clickCount++;
        let elementName = getElementName(e.target);
        trackEvent('click', e.target.tagName.toLowerCase(), elementName, true);
        lastElement = elementName;
    });
    
    // Function to identify element
    function getElementName(element) {
        if (element.closest('[data-testid="stRadio"]')) return 'radio_year';
        if (element.closest('[data-testid="stSelectbox"]')) return 'dropdown_select';
        if (element.closest('.plotly-graph-div')) return 'chart_plotly';
        if (element.closest('button')) return 'button_' + (element.textContent || 'unknown');
        return element.tagName.toLowerCase() || 'unknown';
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
        
        console.log('📤 Sending tracking data:', actionName, elementName);
        
        fetch(API_BASE_URL + '/api/track', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(eventData)
        })
        .then(response => {
            console.log('✅ Tracking response:', response.status);
            return response.json();
        })
        .then(data => console.log('✅ Tracking success:', data))
        .catch(err => {
            console.error('❌ Tracking error:', err);
            errorCount++;
        });
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
        
        fetch(API_BASE_URL + '/api/session', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(sessionData),
            keepalive: true
        }).catch(err => console.error('❌ Session save error:', err));
    }
    
    console.log('✅ User tracking initialized. Session ID:', sessionId);
    </script>
    """
    return tracking_js