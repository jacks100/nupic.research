# Purpose of the Code
This code is intended to run simulations to evaluate the properties of sparse distributed representations (SDRs) with an emphasis on using SDRs for machine learning tasks. The figures generated are automatically saved as PDF files. The properties of SDRs were discussed in the paper "How Can We Be So Dense? The Benefits of Using Highly Sparse Representations" available at https://arxiv.org/abs/1903.11257 and the paper "How do neurons operate on sparse distributed representations? A mathematical theory of sparsity, neurons and active dendrites" available at https://arxiv.org/abs/1601.00720.

# The Code
The following scripts can ben run in any order, but running plot_numerical_results.py may provide some intuition that will make scalar_sdrs.py easier to understand. 

1. plot_effect_of_n.py: Creates a graph of average false positivity rate as a function of N, the dimensionality of the vectors (depreciated). This code requires plotly version 3.10.0.
2. plot_numerical_results.py: Creates a graph of average false positivity rate as a function of N, the dimensionality of the vectors.
3. scalar_sdrs.py: Computes the probability of matching two random SDRs, Xi and Xw, using different values for the matching threshold, theta. 
4. sdr_math_neuron_paper.ipynb: Notebook to run simulations for the sparsity papers and simulations that incorporate SDRs with dendrites.