

#Responds to /save entry command

#1. Gets the current dialog id of user
#2. Searches entry catalogue for an entry with same dialogue_id and isEmbedded=False
#3. Extract the summary and title
#4. Send to Pinecone

#Responds to /QA command

#1. User asks a question about the DB
#2. Gets a response using RetrieverQA