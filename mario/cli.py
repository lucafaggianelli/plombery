import argparse

from mario.orchestrator import orchestrator
from mario.orchestrator.executor import run


def cmd_pipelines(args):
    if args.pipeline_id:
        pass
    else:
        for p in orchestrator.pipelines:
            print("Pipelines:")
            print(f" * {p.id}")


def cmd_run(args):
    pipeline = orchestrator.get_pipeline(args.pipeline_id)

    if not pipeline:
        print(f"Pipeline {args.pipeline_id} doesn't exist")
        return

    # TODO: pass a trigger
    run(pipeline, None)


# create the top-level parser
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

# create the parser for the "foo" command
parser_pipelines = subparsers.add_parser('pipelines')
parser_pipelines.add_argument('pipeline_id', type=str, nargs='?')
parser_pipelines.set_defaults(func=cmd_pipelines)

# create the parser for the "bar" command
parser_run = subparsers.add_parser('run')
parser_run.add_argument('pipeline_id', type=str)
parser_run.set_defaults(func=cmd_run)

# parse the args and call whatever function was selected

def cli():
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    cli()
