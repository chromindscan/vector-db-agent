# #!/bin/bash

# # Simple Vector DB Operations Script

# # Get the blockchain RID
# vector_brid=$(pmc blockchains | jq -r '.[] | select(.Name == "vector_blockchain") | .Rid')
# if [ -z "$vector_brid" ]; then
#     echo "Error: Could not fetch blockchain RID. Using default value."
#     vector_brid="FBD04154EC2F8619376DFDF8671CEB86CAB558C6565C744CE457FD23B1E2D469"
# fi

# # Check for Python script
# VECTOR_PY="./vector-db.py"
# if [ ! -f "$VECTOR_PY" ]; then
#     echo "Error: $VECTOR_PY not found."
#     exit 1
# fi
# chmod +x "$VECTOR_PY" 2>/dev/null

# # Generate embedding vector
# create_vector() {
#     python3 "$VECTOR_PY" "$1"
# }

# # Main menu
# show_menu() {
#     echo "VECTOR DATABASE OPERATIONS"
#     echo "1. Add text to database"
#     echo "2. Search for similar texts"
#     echo "3. Exit"
#     echo
#     echo -n "Enter choice [1-3]: "
#     read choice

#     case $choice in
#         1) add_text ;;
#         2) search_texts ;;
#         3) echo "Exiting."; exit 0 ;;
#         *) echo "Invalid choice."; show_menu ;;
#     esac
# }

# # Add text function
# add_text() {
#     echo "ADD TEXT TO DATABASE"
#     echo
    
#     while true; do
#         echo -n "Enter text (or 'menu' to return): "
#         read user_text
        
#         [ "$user_text" = "menu" ] && show_menu && return
#         [ -z "$user_text" ] && echo "Error: Text cannot be empty." && continue
        
#         echo "Generating embedding..."
#         vector=$(create_vector "$user_text")
        
#         echo "Adding message to chain..."
#         result=$(chr tx -brid $vector_brid add_message "$user_text" "$vector")
        
#         if [[ "$result" == *"CONFIRMED"* ]]; then
#             txid=$(echo "$result" | sed -n 's/.*txid: \([^ ]*\).*/\1/p')
#             echo " ✅ Successfully added! Transaction ID: $txid"
#         else
#             echo " ❌ Failed. Error: $result"
#         fi
#         echo
#     done
# }

# # Search function
# search_texts() {
#     echo "SEARCH SIMILAR TEXTS"
#     echo
    
#     echo -n "Enter search text (or press Enter for default): "
#     read query_text
    
#     if [ -z "$query_text" ]; then
#         query_vector="[1.0, 2.5, 3.0]"
#         echo "Using default vector"
#     else
#         echo "Generating embedding..."
#         query_vector=$(create_vector "$query_text")
#     fi
    
#     echo "Retriving messages from chain with closest vector..."
#     query_result=$(chr query -brid $vector_brid query_closest_objects context=0 q_vector="$query_vector" max_distance=1.0 max_vectors=3 'query_template=["type":"get_messages_with_distance"]')
    
#     echo "Results:"
#     if [ -z "$query_result" ] || [[ "$query_result" == "[]" ]]; then
#         echo "No matches found."
#     else
#         # Simple format - extract and display results
#         echo "$query_result" | grep -o '"text": "[^"]*"\|"distance": "[^"]*"' | 
#             sed 's/"text": "/Text: /g' | 
#             sed 's/"distance": "/Distance: /g' | 
#             sed 's/"//g' | 
#             paste -d ", " - -
#     fi
    
#     echo
#     echo -n "Press Enter to continue..."
#     read
#     show_menu
# }

# # Start program
# show_menu 