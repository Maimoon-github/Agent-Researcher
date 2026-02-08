@echo off
REM Create base directory
mkdir src\nodes\web_scraper

REM Create files in base
echo. > src\nodes\web_scraper\engine.py
echo. > src\nodes\web_scraper\config.py

REM Create spiders directory
mkdir src\nodes\web_scraper\spiders

REM Create middlewares directory and files
mkdir src\nodes\web_scraper\middlewares
echo. > src\nodes\web_scraper\middlewares\rate_limit_middleware.py
echo. > src\nodes\web_scraper\middlewares\proxy_rotation_middleware.py
echo. > src\nodes\web_scraper\middlewares\user_agent_middleware.py
echo. > src\nodes\web_scraper\middlewares\cache_middleware.py

REM Create pipelines directory and files
mkdir src\nodes\web_scraper\pipelines
echo. > src\nodes\web_scraper\pipelines\content_pipeline.py
echo. > src\nodes\web_scraper\pipelines\validation_pipeline.py

REM Create extractors directory and files
mkdir src\nodes\web_scraper\extractors
echo. > src\nodes\web_scraper\extractors\newspaper_extractor.py
echo. > src\nodes\web_scraper\extractors\readability_extractor.py
echo. > src\nodes\web_scraper\extractors\custom_extractor.py
echo. > src\nodes\web_scraper\extractors\pdf_extractor.py

REM Create utils directory and files
mkdir src\nodes\web_scraper\utils
echo. > src\nodes\web_scraper\utils\robots_parser.py
echo. > src\nodes\web_scraper\utils\url_normalizer.py
echo. > src\nodes\web_scraper\utils\content_cleaner.py
echo. > src\nodes\web_scraper\utils\link_analyzer.py

echo Project structure created successfully!
pause
