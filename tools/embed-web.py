from pathlib import Path
p=Path('firmware/cloud_bot_existing_parts');js=(p/'app.js').read_text(encoding='utf8')
(p/'web_app.h').write_text('#pragma once\nconst char APP_JS[] PROGMEM = R"CBJS(\n'+js+'\n)CBJS";\n',encoding='utf8')
