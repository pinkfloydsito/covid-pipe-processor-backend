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
