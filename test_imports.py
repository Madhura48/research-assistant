try:
    from langchain_openai import ChatOpenAI
    print("✓ langchain_openai - OK")
except ImportError as e:
    print(f"✗ langchain_openai - {e}")

try:
    from crewai import Agent, Task, Crew
    print("✓ crewai - OK")
except ImportError as e:
    print(f"✗ crewai - {e}")

try:
    from duckduckgo_search import DDGS
    print("✓ duckduckgo_search - OK")
except ImportError as e:
    print(f"✗ duckduckgo_search - {e}")

try:
    import requests
    print("✓ requests - OK")
except ImportError as e:
    print(f"✗ requests - {e}")

try:
    from bs4 import BeautifulSoup
    print("✓ beautifulsoup4 - OK")
except ImportError as e:
    print(f"✗ beautifulsoup4 - {e}")