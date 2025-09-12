import sources from "../sources.json";

interface Source {
  title: string;
  url: string;
  summary: string;
  published: string;
}

export default function ArticleList() {
  const articles = (sources as Source[])
    .sort((a, b) => new Date(b.published).getTime() - new Date(a.published).getTime())
    .slice(0, 5);

  const stripHtml = (html: string) => html.replace(/<[^>]*>?/gm, "");

  const handleSummaryClick = (level: string, summary: string) => {
    alert(`${level} summary: ${stripHtml(summary)}`);
  };

  return (
    <section>
      <h2>Latest Articles</h2>
      <div className="articles">
        {articles.map((article) => (
          <div key={article.url} className="card">
            <h3>{article.title}</h3>
            <p dangerouslySetInnerHTML={{ __html: article.summary }} />
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Read article
            </a>
            <div className="level-buttons">
              {["Novice", "Intermediate", "Expert"].map((level) => (
                <button
                  key={level}
                  onClick={() => handleSummaryClick(level, article.summary)}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
