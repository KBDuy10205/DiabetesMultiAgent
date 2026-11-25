import json
import sys
from .workflow import AgentWorkflow


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        request = json.load(sys.stdin)
        result = AgentWorkflow().run(request)
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if any(agent['status'] == 'error' for agent in result['agents'].values()) or (result['answer'] and not result['answer']['valid']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
