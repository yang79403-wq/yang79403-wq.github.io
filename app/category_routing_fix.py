from datetime import datetime, timezone
import category_routing

category_routing.NOW = datetime.now(timezone.utc).isoformat(timespec='seconds')
category_routing.main()
