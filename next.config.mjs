const repoName = "signal"; // change to repo name

export default {
  output: "export",                    // enables static export
  trailingSlash: true,                 // safer for GH Pages
  images: { loader: "akamai", path: "" }, // static-compatible images
  assetPrefix: process.env.NODE_ENV === "production" ? `/${repoName}/` : "",
  basePath: process.env.NODE_ENV === "production" ? `/${repoName}` : "",
  reactStrictMode: true,
};
