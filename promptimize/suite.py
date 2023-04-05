from promptimize import utils


class Suite:
    """a collection of use cases to be tested"""

    def __init__(self, prompts, model_id="text-davinci-003", max_tokens=1000):
        self.prompts = {o.key: o for o in prompts}
        self.model_id = model_id
        self.max_tokens = max_tokens

    def execute(self, verbose=False, style="yaml", model_id=None, max_tokens=None):
        model_id = model_id or self.model_id
        max_tokens = max_tokens or self.max_tokens
        for prompt in self.prompts.values():
            prompt.run(model_id=model_id, max_tokens=max_tokens)
            prompt.test()
            prompt.print(verbose=verbose, style=style)
            print("#" + "-" * 40)
        print(utils.serialize_object(self._serialize_run_summary(), style))

    def _serialize_run_summary(self, verbose=False):
        prompts = self.prompts.values()
        tested = [p for p in prompts if p.was_tested]
        suite_score = None
        if len(tested) > 0:
            suite_score = sum([p.test_results_avg for p in tested]) / len(tested)
        d = {"suite_score": suite_score}
        return d
