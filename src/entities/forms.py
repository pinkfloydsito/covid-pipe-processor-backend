import re
from django import forms
from entities.models import CovidPipe


class CovidPipeForm(forms.ModelForm):
    range_pipes = forms.CharField(required=False)

    def save(self, commit=True):
        range_pipes = self.cleaned_data.get('range_pipes', None)
        if not range_pipes:
            return super(CovidPipeForm, self).save(commit=commit)

        last_movement = self.cleaned_data.get('last_movement', None)
        instance = super(CovidPipeForm, self).save(commit=False)

        try:
            numbers = range_pipes.split('-')
            match_0 = re.match(r"([a-z]+)([0-9]+)", numbers[0], re.I)
            match_1 = re.match(r"([a-z]+)([0-9]+)", numbers[1], re.I)
            items_0 = None
            if match_0:
                items_0 = match_0.groups()

            items_1 = None
            if match_1:
                items_1 = match_1.groups()
            
            if match_0 and match_1:
                for i in range(int(items_0[1]), int(items_1[1])+1):
                    CovidPipe.objects.create(
                        name="{}{}".format(items_0[0], str(i)),
                        last_movement=last_movement)
                
            else:
                for i in range(int(numbers[0]), int(numbers[1])+1):
                    CovidPipe.objects.create(
                        name=str(i),
                        last_movement=last_movement)

        except Exception as e:
            raise(e)

        return instance

    class Meta:
        model = CovidPipe
        fields = '__all__'
