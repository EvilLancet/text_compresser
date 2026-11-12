import asyncio
from app.schemas import CompressRequest
from app.ollama_client import generate_text, timeout

class AiQueue:
    def __init__(self, worker):
        self._queue = asyncio.Queue()
        self._worker = worker
        self._active = False
        self._task = None
        self.stop_list = []
        self._current_user = None
        self._current_task = None

    @property
    def active(self):
        return self._active

    def get_wait_time(self):
        return int((self._queue.qsize() + 1)*timeout.read)
    
    async def add_request(self, payload: CompressRequest):
        future = asyncio.get_running_loop().create_future()
        await self._queue.put((payload, future, payload.user_id))
        if not self._active:
            await self.start()
        return await future

    def cancel(self, user_id):
        if self._current_user == user_id and self._current_task:
            self._current_task.cancel()
        else:
            self.stop_list.append(user_id)

    async def start(self):
        if self._active:
            return
        self._active = True
        self._task = asyncio.create_task(self._process())

    async def _process(self):
        while True:
            payload, future, user_id = await self._queue.get()

            # Пользователь уже отменил — просто пропускаем
            if user_id in self.stop_list:
                self.stop_list.remove(user_id)
                if not future.done():
                    future.set_result("")  # или "Отменено"
                self._queue.task_done()

                if self._queue.empty():
                    self._active = False
                    break
                continue

            self._current_user = user_id

            try:
                self._current_task = asyncio.create_task(self._worker(payload))
                result = await self._current_task

                if not future.done():
                    # На всякий случай ещё раз проверяем отмену
                    if user_id in self.stop_list:
                        future.set_result("")
                    else:
                        future.set_result(result)

            except asyncio.CancelledError:
                # Worker прервали через cancel()
                if not future.done():
                    future.set_result("")
            except Exception as e:
                if not future.done():
                    future.set_result("")  # или можно пробросить ошибку
            finally:
                self._current_user = None
                self._current_task = None

                if user_id in self.stop_list:
                    self.stop_list.remove(user_id)

                self._queue.task_done()

            if self._queue.empty():
                self._active = False
                break

ai_queue = AiQueue(worker=generate_text)