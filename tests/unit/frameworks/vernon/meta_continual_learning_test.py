# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2020, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------


import unittest

import torch

from nupic.research.frameworks.continual_learning.maml_utils import clone_model
from nupic.research.frameworks.vernon import MetaContinualLearningExperiment

# Retrieve function that updates params in place.
# This enables taking gradients of gradients.
update_params = MetaContinualLearningExperiment.update_params


class Quadractic(torch.nn.Module):
    """Quadratic layer: Computes W^T W x"""
    def __init__(self):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor([
            [0.94, 0.07],
            [0.40, 0.21]
        ]))

    def forward(self, x):
        """Compute W^T W x"""
        out = torch.matmul(self.weight, x)
        out = torch.matmul(self.weight.transpose(1, 0), out)
        return out


class GradsOfGradsTest(unittest.TestCase):
    """
    Perform tests for taking gradients of gradients. Specifically, this uses a
    quadratic layer as a test example since it yields non-trivial results (unlike a
    linear layer) and enables hand derived expected values.
    """

    def setUp(self):
        # Input passed to quadratic function: a W^T W x
        self.left_input = torch.tensor([[1., 1.]], requires_grad=True)  # a
        self.right_input = torch.tensor([[0.32], [0.72]], requires_grad=True)  # x

        # Expected gradient of gradient for quadratic layer updated via SGD.
        self.expected_grad = torch.tensor([[0.3972, 0.6762], [0.2869, 0.4458]])

    def test_auto_grad_with_quadratic_function(self):
        """
        Test use of pytorch's autograd to keep track of gradients of gradients.

        This validates the hand derived solution of self.expected_grad.
        """

        # Use the predefined weight from the quadratic layer.
        weight = Quadractic().weight

        # First forward pass: Loss = a W^T W x
        a = self.left_input
        x = self.right_input
        loss = torch.matmul(weight, x)
        loss = torch.matmul(weight.transpose(1, 0), loss)
        loss = torch.matmul(a, loss)

        # First backward pass.
        loss.backward(retain_graph=True, create_graph=True)
        weight.grad

        # Compare the manually computed expected 2nd derivative with pytorch's autograd.
        #   W' = W * (x·a + (x·a)^T)
        with torch.no_grad():
            m = torch.matmul(x, a)
            m = m + m.transpose(1, 0)
            w_grad_expected = torch.matmul(weight, m)
        self.assertTrue(weight.grad.allclose(w_grad_expected, atol=1e-8))

        # Update weight
        lr = 0.1
        weight2 = weight - lr * weight.grad
        weight2.retain_grad()

        # Zero the gradient of the non-updated weight.
        weight.grad = None

        # Second forward pass.
        loss2 = torch.matmul(weight2, x)
        loss2 = torch.matmul(weight2.transpose(1, 0), loss2)
        loss2 = torch.matmul(a, loss2)
        loss2.backward()

        # Compare the manually computed expected 2nd derivative with pytorch's autograd.
        #   W'  = W2' · (I - lr(x·a + (x·a)^T))
        #   W2' = W2  · (x·a + (x·a)^T)
        m = torch.matmul(x, a)
        m = m + m.transpose(1, 0)
        w2_grad_expected = torch.matmul(weight2, m)
        w_grad_expected = torch.matmul(w2_grad_expected, (torch.eye(2) - lr * m))
        self.assertTrue(weight.grad.allclose(w_grad_expected, atol=1e-8))
        self.assertTrue(weight2.grad.allclose(w2_grad_expected, atol=1e-8))

        # Compare pytorch's 2nd derivative with the one saved by this test class.
        self.assertTrue(weight.grad.allclose(self.expected_grad, atol=1e-4))

    def test_update_params_with_quadratic_layer(self):
        """
        Test use of update_params function.

        It should update the parameters in a way that enables taking
        a gradient of a gradient.
        """

        quad = Quadractic()
        quad_clone = clone_model(quad)
        x = self.right_input

        # First forward and backward pass: akin to the inner loop in meta-cl.
        out = quad_clone(x)
        loss = out.sum()
        update_params(quad_clone.named_parameters(), quad_clone, loss, lr=0.1)

        # Second forward and backward pass: akin to the outer loop in meta-cl.
        out2 = quad_clone(x)
        loss2 = out2.sum()
        loss2.backward()

        # Validate gradient on original weight parameter.
        self.assertTrue(torch.allclose(quad.weight.grad, self.expected_grad, atol=1e-4))


if __name__ == "__main__":
    unittest.main(verbosity=2)
