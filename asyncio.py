import asyncio

async def main():
    result = await chatbot.ainvoke(
        {"messages": ["hello"]},
        config={"configurable": {"thread_id": "t1"}}
    )
    print(result)

asyncio.run(main())
