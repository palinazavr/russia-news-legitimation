# Russia in European war coverage: collection, coding and analysis code

Code for the second article of the dissertation on the legitimation and delegitimation of Russia in the press of four European countries (Germany, Spain, Poland, Hungary), 2022-2026. Eight outlets, 48,325 articles, each coded by a vision-language model from its full text and all images against a 14-category codebook.

The annotations, codebook and filter flags are published separately as a dataset: https://doi.org/10.5281/zenodo.23212562.

The tables in the dataset are derived from the output of `05_results/results.ipynb` (the article and activation tables).

## Pipeline

| Folder | Content |
|---|---|
| `01_collection/` | Retrieval of article addresses from sitemaps and archive pages, and download of article metadata, texts and images, by country. |
| `02_keyword_filtering/` | One notebook per outlet. Keyword filtering of the collected articles and linking of each article to its image files. |
| `03_preprocessing/` | Normalisation of columns, the headline filter for Russia-central articles, repair and completion of missing texts, dates and images, removal of duplicate and junk images, and the audit of the final data files. |
| `04_annotation/` | The final coding run with Qwen3-VL-32B-Instruct through OpenRouter. |
| `05_results/` | Construction of the activation and article tables from the model output, descriptive statistics, hypothesis tests and figures. |
| `codebook/` | The coding manual and instructions sent in every request. |

Run the folders in numerical order. Inside `01_collection` and `02_keyword_filtering` the notebooks for different outlets are independent of each other.

## Files the notebooks expect

The notebooks read and write files by bare file name in the working directory, for example `eldiario_final_data_v2.csv` and `eldiario_results_final.csv`. Copy the files a notebook needs next to it, or start Jupyter in a folder that holds them. `04_annotation/annotation_run.ipynb` reads `codebook_updated21.8.txt` and `instruction_text.txt` from the working directory, so copy both from `codebook/`.

Article texts and images are not part of the repository, and the notebooks hold no outputs, so no article text is stored in them.

## Annotation settings

Model `qwen/qwen3-vl-32b-instruct`, temperature 0, top_p 1, frequency and presence penalty 0, seed 42, JSON output. One request per article with the codebook and instructions, the headline, the complete text and all images (longer side at most 1,024 pixels, JPEG quality 85). The API key is read from the environment variable `openrouter_api_key`.

## Setup

```
pip install -r requirements.txt
```

## Notes

The notebooks are the working notebooks of the project. The scrapers depend on the page structure of each outlet as it was in 2026, and the sites may have changed since. Paths in the notebooks were generalised to bare file names when the repository was prepared.

## License

MIT, see `LICENSE`.

## Citation

Smirnova, P. (2026). Code for the analysis of Russia's representation in European war coverage [Software]. See `CITATION.cff`.
