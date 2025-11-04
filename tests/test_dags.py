import pytest

from plombery import Pipeline, task


def test_pipeline_context_manager_adds_tasks():
    with Pipeline(id="pipeline1") as p:

        @task
        def task1():
            pass

        @task
        def task2():
            pass

        @task
        def task3():
            pass

        task1 >> task2 >> task3

        assert p.tasks == [task1, task2, task3]


def test_cyclic_dependencies_identified():
    with pytest.raises(ValueError) as e:
        with Pipeline(id="pipeline1"):

            @task
            def task1():
                pass

            @task
            def task2():
                pass

            @task
            def task3():
                pass

            task1 >> task2 >> task3 >> task1

    assert "Pipeline 'pipeline1' contains a cyclic dependency and cannot run." in str(
        e.value
    )
