#!/usr/bin/env python3
"""
Transform index.html → modules/globe.html
Removes: header, statusbar, JARVIS chat panel, settings panel
Adds: postMessage communication with parent shell
"""
import re, sys, os

def transform(html):
    # 1. Remove the header bar
    html = re.sub(
        r'<!-- HEADER -->.*?</div>\s*\n',
        '<!-- Header removed — shell provides this -->\n',
        html, count=1, flags=re.DOTALL
    )

    # 2. Remove status bar
    html = re.sub(
        r'<!-- STATUS BAR -->.*?</div>\s*\n',
        '<!-- Status bar removed — shell provides this -->\n',
        html, count=1, flags=re.DOTALL
    )

    # 3. Remove JARVIS chat panel
    html = re.sub(
        r'<!-- JARVIS CHAT -->.*?</div>\s*\n\s*</div>\s*\n',
        '<!-- JARVIS chat removed — shell provides this -->\n',
        html, count=1, flags=re.DOTALL
    )

    # 4. Remove Settings panel
    html = re.sub(
        r'<!-- SETTINGS -->.*?</div>\s*\n\s*</div>\s*\n',
        '<!-- Settings removed — shell provides this -->\n',
        html, count=1, flags=re.DOTALL
    )

    # 5. Remove JARVIS and Settings toolbar buttons
    html = html.replace(
        """<button class="tb-btn" onclick="togglePanel('Jarvis')"><span class="dot" style="background:var(--cyan)"></span>JARVIS</button>""",
        '<!-- JARVIS button removed -->'
    )

    # 6. Remove settings toolbar button
    html = re.sub(
        r'<button class="tb-btn" onclick="togglePanel\(\'Settings\'\)">.*?</button>',
        '<!-- Settings button removed -->',
        html
    )

    # 7. Remove the saveGroqKey and updateAiStatus functions (shell handles these)
    # These will cause errors since the DOM elements are gone, so we stub them
    stub_functions = """
/* ====== SHELL COMMUNICATION ====== */
// Stub functions (handled by parent shell)
function saveGroqKey(){}
function updateAiStatus(){}

// Send data to parent shell
function notifyShell(type, data) {
  try { window.parent.postMessage({type, data}, '*'); } catch(e) {}
}

// Listen for commands from shell
window.addEventListener('message', function(e) {
  if (e.data.type === 'FLY_TO' && e.data.code) {
    const info = COUNTRY_INFO[e.data.code];
    if (info && globe) globe.pointOfView({lat:info.lat, lng:info.lng, altitude:1.8}, 1000);
  }
  if (e.data.type === 'TOGGLE_LAYER' && e.data.layer) {
    activeLayers[e.data.layer] = !activeLayers[e.data.layer];
    updateArcs();
  }
  if (e.data.type === 'MARKET_DATA') {
    // Receive shared market data from shell
  }
});

// Override sendJarvisMsg to route through shell
function sendJarvisMsg() {
  var input = document.getElementById('jcInput');
  if (!input) return;
  var msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  notifyShell('JARVIS_QUERY', msg);
}
"""

    # Insert before the INIT section
    html = html.replace('/* ====== INIT ====== */', stub_functions + '\n/* ====== INIT ====== */')

    # 8. After fetchNews completes, notify shell
    html = html.replace(
        "document.getElementById('stNews').textContent=`INTEL: ${items.length} ITEMS`;",
        "document.getElementById('stNews').textContent=`INTEL: ${items.length} ITEMS`;\n  notifyShell('NEWS_DATA', items.map(n=>({title:n.title,src:n.src,sentiment:n.sentiment})));"
    )

    # 9. After fetchMarkets completes, notify shell
    html = html.replace(
        "document.getElementById('stMkts').textContent=`MARKETS: ${Object.keys(allMarketData).length} FEEDS`;",
        "document.getElementById('stMkts').textContent=`MARKETS: ${Object.keys(allMarketData).length} FEEDS`;\n  notifyShell('MARKET_DATA', allMarketData);"
    )

    # 10. Adjust .app height to not include missing header/statusbar
    # The globe should fill the entire iframe
    html = html.replace('.hd{height:40px;', '.hd{height:0px;display:none;')

    return html

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'modules/globe.html'

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        print(f"Usage: python3 {sys.argv[0]} <input_index.html> <output_globe.html>")
        print(f"\nRun this in your JarvisEye repo directory:")
        print(f"  mkdir -p modules")
        print(f"  python3 transform_globe.py index.html modules/globe.html")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        html = f.read()

    result = transform(html)

    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"✓ Transformed {input_file} → {output_file}")
    print(f"  Removed: header, statusbar, JARVIS chat, settings")
    print(f"  Added: postMessage communication with shell")
    print(f"  Original size: {len(html)} chars")
    print(f"  Module size: {len(result)} chars")