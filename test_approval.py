import time

from notifications.notification import (
    send_visitor_photo,
    check_user_decision
)


IMAGE_PATH = "captured_visitors/visitor_20261005_110635.jpg"


print()
print("================================")
print("   TELEGRAM APPROVAL TEST")
print("================================")
print()


# Send visitor request
if not send_visitor_photo(IMAGE_PATH):

    print("❌ Could not send visitor request.")
    exit()


print()
print("================================")
print("WAITING FOR YOUR DECISION")
print("================================")
print()
print("Open Telegram.")
print("Press ACCEPT or REJECT.")
print()


last_update_id = 0


while True:

    decision, last_update_id = check_user_decision(
        last_update_id
    )

    if decision == "ACCEPT":

        print()
        print("================================")
        print("       ✅ ACCESS GRANTED")
        print("================================")
        break


    if decision == "REJECT":

        print()
        print("================================")
        print("       ❌ ACCESS DENIED")
        print("================================")
        break


    time.sleep(1)