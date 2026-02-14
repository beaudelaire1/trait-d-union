(function () {
  if (!window.tinymce) {
    return;
  }

  tinymce.init({
    selector: "textarea.tus-tinymce",
    menubar: false,
    branding: false,
    height: 480,
    plugins: "lists link table code charmap",
    toolbar:
      "undo redo | formatselect | bold italic underline | alignleft aligncenter alignright alignjustify | forecolor backcolor | bullist numlist | link table | removeformat | code",
    block_formats:
      "Paragraph=p; Heading 2=h2; Heading 3=h3; Quote=blockquote",
    forced_root_block: "p",
    content_style:
      "body { font-family: Space Grotesk, Arial, sans-serif; color: #F6F7FB; background: #0D1016; line-height: 1.7; } " +
      "p { margin: 0 0 1rem; text-align: justify; } " +
      "h2 { font-size: 1.4rem; margin: 1.5rem 0 0.8rem; } " +
      "h3 { font-size: 1.2rem; margin: 1.2rem 0 0.6rem; } " +
      "a { color: #0B2DFF; text-decoration: underline; }",
    skin: "oxide",
    content_css: false,
  });
})();
