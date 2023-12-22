import time
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        request_start_time = time.time()
        print(f"Request received: {environ.get('PATH_INFO')} at {self._get_current_time()}.")

        def custom_start_response(status, headers, exc_info=None):
            print(f"Request processed: {status} at {self._get_current_time()}")
            return start_response(status, headers, exc_info)

        response = self.app(environ, custom_start_response)

        request_end_time = time.time()
        elapsed_time = request_end_time - request_start_time
        print(f"Request completed in {elapsed_time:.6f} seconds.")

        return response

    def _get_current_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    
