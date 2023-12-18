class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        print(f"Request received: {environ.get('PATH_INFO')}.")

        def custom_start_response(status, headers, exc_info=None):
            print(f"Request processed: {status}")
            return start_response(status, headers, exc_info)
        
        return self.app(environ, custom_start_response)