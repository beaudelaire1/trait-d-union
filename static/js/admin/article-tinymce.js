(function () {
  if (!window.tinymce) {
    return;
  }

  tinymce.init({
    selector: "textarea.tus-tinymce",
    menubar: false,
    branding: false,
    height: 520,
    plugins: "lists link table code charmap",
    toolbar:
      "undo redo | formatselect | bold italic underline | alignleft aligncenter alignright alignjustify | forecolor backcolor | bullist numlist | link table | removeformat | code",
    block_formats:
      "Paragraphe=p; Titre 2=h2; Titre 3=h3; Titre 4=h4; Citation=blockquote",
    forced_root_block: "p",
    valid_elements:
      "p[style],br,strong/b,em/i,u,sub,sup,span[style],div[style]," +
      "ul,ol,li," +
      "a[href|title|target]," +
      "h2[style],h3[style],h4[style],h5[style],h6[style]," +
      "blockquote[style],code[class],pre[class],hr," +
      "img[src|alt|title|width|height|loading|style]," +
      "figure,figcaption," +
      "table,thead,tbody,tr,td[colspan|rowspan|style],th[colspan|rowspan|style]",
    content_style:
      "body { font-family: Space Grotesk, Arial, sans-serif; color: #F6F7FB; background: #0D1016; line-height: 1.7; } " +
      "p { margin: 0 0 1rem; text-align: justify; } " +
      "h2 { font-size: 1.4rem; margin: 1.5rem 0 0.8rem; } " +
      "h3 { font-size: 1.2rem; margin: 1.2rem 0 0.6rem; } " +
      "h4 { font-size: 1.1rem; margin: 1rem 0 0.5rem; } " +
      "blockquote { border-left: 3px solid #0B2DFF; padding: 0.5em 1em; margin: 1em 0; font-style: italic; } " +
      "a { color: #0B2DFF; text-decoration: underline; } " +
      "table { border-collapse: collapse; width: 100%; } " +
      "td, th { border: 1px solid rgba(246,247,251,0.15); padding: 0.4em 0.8em; }",
    skin: "oxide",
    content_css: false,
  });
})();
