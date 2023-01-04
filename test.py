import asyncio

async def call():
    sum = 0
    for i in range(10):
        await asyncio.sleep(1)
        sum += i

async def after():
    await call()
    print('call is done')

def main():
    asyncio.run(after())

if __name__ == "__main__":
    main()
    