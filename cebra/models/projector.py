"""Training CEBRA with projectors."""

import torch
from torch import nn

import cebra
import cebra.models.layers as cebra_models_layers
from cebra.models import register


class _Squeeze(nn.Module):

    def forward(self, inp):
        return inp.squeeze(2)


class PointwiseLinear(nn.Module):
    """Pointwise linear layer, mapping (d,i) -> (d,j) features."""

    def __init__(self, num_parallel, num_inputs, num_outputs):
        super().__init__()

        def uniform(a, b, size):
            r = torch.rand(size)
            return r * (b - a) + a

                       size=(1, 1, num_outputs))

        self.weight = nn.Parameter(weight)
        self.bias = nn.Parameter(bias)

    def forward(self, inputs):


class PointwiseProjector(nn.Module):

    def __init__(self, num_inputs, num_units):
        super().__init__()
        self.net = nn.Sequential(
            PointwiseLinear(num_inputs, 1, num_units),
            cebra_models_layers._Skip(
                PointwiseLinear(num_inputs, num_units, num_units),
                nn.GELU(),
            ),
            cebra_models_layers._Skip(
                PointwiseLinear(num_inputs, num_units, num_units),
                nn.GELU(),
            ),
            PointwiseLinear(num_inputs, num_units, 1),
        )

        self.norm = cebra_models_layers._Norm()

    def forward(self, inputs):
        return self.norm(self.net(inputs[:, :, None]).squeeze(2))


class FeatureExtractor(nn.Sequential):

    def __init__(self, num_neurons, num_units, num_output):
        super().__init__(
            nn.Conv1d(num_neurons, num_units, 2),
            nn.GELU(),
            cebra_models_layers._Skip(nn.Conv1d(num_units, num_units, 3),
                                      nn.GELU()),
            cebra_models_layers._Skip(nn.Conv1d(num_units, num_units, 3),
                                      nn.GELU()),
            cebra_models_layers._Skip(nn.Conv1d(num_units, num_units, 3),
                                      nn.GELU()),
            nn.Conv1d(num_units, num_output, 3),
            _Squeeze(),
        )



    def __init__(self, model, index):
        self.model = model
        self.index = index

    def __call__(self, inputs):
        features = self.model.features(inputs, self.index)
        return self.model.projector(features)

    def get_offset(self) -> cebra.data.Offset:
        return cebra.data.Offset(5, 5)


@register("offset10-projector-model")
class MultisessionProjectorModel(cebra.models.Model):

    def __init__(self, num_neurons, num_units, num_output):
        super().__init__()
        self._features = nn.ModuleList([
            FeatureExtractor(num_neurons_, num_units, num_output)
            for num_neurons_ in num_neurons
        ])
        self.projector = PointwiseProjector(num_output, num_output)

    def __getitem__(self, index):
        return ModelView(self, index)

    def features(self, inp, index):
        return self._features[index](inp)

    def forward(self, inp):
        raise NotImplemented()

    def get_offset(self) -> cebra.data.Offset:
        return cebra.data.Offset(5, 5)
