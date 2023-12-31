import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.chains import RetrievalQA
from langchain.vectorstores import Pinecone
import config
import pandas as pd
from uuid import uuid4
import utils
import time


pinecone.init(
    api_key=config.pinecone_api_key,
    environment=config.pinecone_env
)

class Index:
    def __init__(self, index_name: str, user_id: str):
        self.index_name = index_name
        self.user_id = user_id
        self.embedding_model_name='text-embedding-ada-002'
        self.index=self.create_index_if_not_exists()
        self.embed = OpenAIEmbeddings(
            model=self.embedding_model_name,
            openai_api_key=config.openai_api_key
        )
        self.text_field = 'text'
        self.vectorstore = Pinecone(
            self.index, self.embed.embed_query, self.text_field
        )
        self.entry_summary=""
        self.entry_title=""
    
    #TODO: Get this function into openai_utils when converting everything to langchain
    def get_answer(self, message, user_id):
        # chat completion llm
        llm = ChatOpenAI(
            openai_api_key=config.openai_api_key ,
            model_name='gpt-3.5-turbo',
            temperature=0.3
        )
        # conversational memory
        conversational_memory = ConversationBufferWindowMemory(
            memory_key='chat_history',
            k=5,
            return_messages=True
        )
        # retrieval qa chain
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever()
        )
        qa.retriever.search_kwargs = {
            "filter": {"user_id": {"$eq": user_id}}
        }
        answer = qa.run(message)
        return answer
    
    def push_to_index(self, entry: dict):

        self.entry_summary=entry["summary"]["choices"][0]["message"]["content"]
        self.entry_title=entry["title"]["choices"][0]["message"]["content"]

        vector_count_old=self.index.describe_index_stats()["total_vector_count"]

        data = self.get_prepared_data()
        self.index = pinecone.GRPCIndex(self.index_name)
        batch_size = 100

        for i in range(0, len(data), batch_size):
            # get end of batch
            i_end = min(len(data), i+batch_size)
            batch = data.iloc[i:i_end]

            # first get metadata fields for this record
            metadatas = [{
            'text' : record[1],  # 'text' will contain the same data as 'context'
            'user_id' : record[2],
            'title' : record[3]
            } for record in batch.itertuples(index=False)]

            # print(metadatas)
            # get the list of contexts / documents
            documents = batch['context'].tolist()

            # create document embeddings
            embeds = self.embed.embed_documents(documents)

            # get IDs and convert them to strings
            ids = batch['uuid'].astype(str).tolist()

            # add everything to pinecone
            self.index.upsert(vectors=list(zip(ids, embeds, metadatas)))

        # switch back to normal index for langchain
        self.index = pinecone.Index(self.index_name)

        while self.index.describe_index_stats()["total_vector_count"]==vector_count_old:
            time.sleep(5)
        
        return True

        # self.vectorstore = Pinecone(
        #     index, embed.embed_query, text_field
        # )

    def create_index_if_not_exists(self):
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                metric='dotproduct',
                dimension=1536  # 1536 dim of text-embedding-ada-002
            )
        index=pinecone.Index(self.index_name)
        return index
    
    def get_prepared_data(self):
        grouped_data = utils.group_bodies_into_chunks(self.entry_summary, 100)
        data = pd.DataFrame(grouped_data, columns=['context'])
        data['user_id']= self.user_id
        data['title'] = self.entry_title
        data['uuid'] = [uuid4() for _ in range(len(data.index))]
        data.drop_duplicates(subset='context', keep='first', inplace=True)

        # Reset index and ensure 'index' column is added
        data = data.reset_index(drop=True)
        data = data.reset_index()
        
        return data
    
