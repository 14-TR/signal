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

  return (
    <section>
      <h2>Latest Articles</h2>
      <div className="articles">
        {articles.map((article) => (
          <a key={article.url} href={article.url} className="card" target="_blank" rel="noopener noreferrer">
            <h3>{article.title}</h3>
            <p>{article.summary}</p>
          </a>
        ))}
      </div>
    </section>
  );
}
