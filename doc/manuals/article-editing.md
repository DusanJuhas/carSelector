# Article editing — author's manual

This manual is for **authors** of the Rovis articles portal: how to get the author role, write and
format an article, write it in Czech and/or English, choose who can read it, and publish, edit or
delete it.

The article editor is the WYSIWYG editor from the **[NiceGUI](https://nicegui.io/)** UI library
(`ui.editor`), which wraps **Quasar's [QEditor](https://quasar.dev/vue-components/editor)** component
(Quasar is the Vue.js component framework NiceGUI is built on). Text is formatted the way it will look
to readers, and the editor stores the article as HTML. No separate editor library or plugin is used.

The UI is in Czech by default and can be switched to English. This manual quotes the **Czech label**
first, with the English label in parentheses: **Uložit koncept** (*Save draft*).

---

## Contents

1. [Getting the author role](#1-getting-the-author-role)
2. [Where to find your articles](#2-where-to-find-your-articles)
3. [Creating a new article](#3-creating-a-new-article)
4. [Language versions (Czech / English)](#4-language-versions-czech--english)
5. [Formatting text — the toolbar](#5-formatting-text--the-toolbar)
6. [Links, images and HTML source](#6-links-images-and-html-source)
7. [Who can read the article (visibility)](#7-who-can-read-the-article-visibility)
8. [Saving and publishing](#8-saving-and-publishing)
9. [Editing an existing article](#9-editing-an-existing-article)
10. [Deleting an article](#10-deleting-an-article)
11. [What readers see](#11-what-readers-see)
12. [Limits and error messages](#12-limits-and-error-messages)
13. [Tips and known limitations](#13-tips-and-known-limitations)

---

## 1. Getting the author role

Only users with the **author role** (and administrators) can write articles.

1. Log in. Click **Přihlásit se** (*Log in*), enter your email, then enter the six-digit code the app
   emails to you. No password is needed, and an account is created on first login.
2. Open the account menu in the header and choose **Stát se autorem** (*Become an author*).
3. Fill in **Jméno, pod kterým budete publikovat** (*The name you'll publish under*). This is your
   byline on every article (max. 120 characters). Optionally add a message for the administrator.
4. Click **Odeslat žádost** (*Send request*).

An administrator approves or rejects the request in the admin console (tab **Autoři** / *Authors*).
Reopening the dialog shows the request's state: pending, or rejected (you can then send a new one).
Once approved, the account menu and the portal's top bar show **Moje články** (*My articles*).

> **Administrators** can write articles without the author role. An admin who never chose a byline is
> shown as **Redakce Rovis** (*Rovis editorial team*).

If an administrator later revokes your role, your published articles stay readable, but you can no
longer edit, publish or delete them.

## 2. Where to find your articles

| Page | Address | What it shows |
|---|---|---|
| **Moje články** (*My articles*) | `/author` | All your articles, drafts included, most recently edited first |
| New article | `/author/new` | An empty editor |
| Edit article | `/author/edit/<id>` | The editor with an existing article |
| **Články** (*Articles*) | `/articles` | The public reader view: everything you're allowed to read |

Each row in **Moje články** shows:

- the title (in your current UI language if that version exists, else in the other language);
- **Upraveno** (*Edited*) and the date of the last save;
- a badge for each language version the article has: **CS**, **EN**, or both;
- a visibility badge: **Jen já (koncept)** (*Only me (draft)*), **Vybraní uživatelé** (*Selected
  users*) or **Všichni** (*Everyone*).

Click a row to open the article in the editor.

## 3. Creating a new article

1. Go to **Moje články** and click **Nový článek** (*New article*).
2. Pick the language tab (see [section 4](#4-language-versions-czech--english)). The editor opens on
   your current UI language.
3. Type the **Nadpis** (*Title*), up to 200 characters.
4. Write the body in the large text area below the toolbar. Until you type, it shows the placeholder
   **Začněte psát…** (*Start writing…*).
5. Choose who can read it (see [section 7](#7-who-can-read-the-article-visibility)).
6. Click **Uložit koncept** (*Save draft*) or **Publikovat** (*Publish*). The button's label follows
   the selected visibility.

After the first save the address changes to `/author/edit/<id>`, so later saves update the same
article and a page reload keeps it open.

## 4. Language versions (Czech / English)

Every article can have a **Czech version, an English version, or both**. Each version has its own
title and body. Visibility, readers and dates are shared by the whole article.

The editor has one tab per language, above the title field:

- **Čeština** / **Angličtina** (*Czech* / *English*).
- A tab whose title is still empty is labelled **(prázdné)** (*(empty)*), for example
  **Angličtina (prázdné)**. The label updates as you type the title.
- When you edit an existing article, the editor opens on the version shown in the list: your UI
  language if the article has it, otherwise the language it exists in.

Rules applied when you save:

| Tab state | Result |
|---|---|
| Title **and** text filled in | The version is saved |
| Title filled in, text empty | The version is saved (with an empty body) |
| Text filled in, **no title** | Not saved: error **Doplňte prosím nadpis (verze: …)** (*Please add a title (version: …)*), and the editor switches to that tab |
| Both empty | No version in this language. If the version existed before, it is **removed** |
| All tabs empty | Not saved: error **Vyplňte prosím nadpis a text aspoň jedné jazykové verze.** (*Please fill in the title and text of at least one language version.*) |

A body counts as empty when it has no visible text and no image. Leftover editor markup such as an
empty line doesn't count.

**One version is enough.** Readers of the other language get the existing version with a notice (see
[section 11](#11-what-readers-see)). To add a translation later, open the article, fill in the empty
tab and save. To remove a translation, clear its title and text and save.

> Your input in both tabs is kept while you switch between them, but nothing is saved until you click
> the save/publish button.

## 5. Formatting text — the toolbar

The toolbar above the text area has these groups, from left to right:

| Group | Buttons | What they do |
|---|---|---|
| Inline formatting | **B**, *I*, U, ~~S~~ | Bold, italic, underline, strikethrough on the selected text |
| Block type | H2, H3, P | Turns the current paragraph into a heading (level 2 or 3) or back into a normal paragraph |
| Lists and indentation | bulleted list, numbered list, quote, outdent, indent | Bulleted (`•`) and numbered lists, a block quotation, decrease / increase indentation (also nests list items) |
| Alignment | left, center, right, justify | Paragraph alignment |
| Insert / clean up | link, horizontal rule, remove formatting | See [section 6](#6-links-images-and-html-source); the rule inserts a dividing line; **remove formatting** clears inline formatting from the selection |
| History | undo, redo | Undo / redo your last edits |
| Source | `<>` | Switches between the formatted view and the raw HTML (see below) |

Hover over a button to see its tooltip.

Usual browser shortcuts also work in the text area: **Ctrl+B** (bold), **Ctrl+I** (italic), **Ctrl+U**
(underline), **Ctrl+Z** / **Ctrl+Y** (undo / redo). Use **Cmd** instead of Ctrl on macOS.

Style guidance:

- The article title is already the page's main heading. Inside the body, start sections with
  **H2** and subsections with **H3**. Don't use bold paragraphs as headings.
- The editor uses the same typography as the reader view, so the article looks to readers the way
  you see it while writing.

## 6. Links, images and HTML source

**Links.** Select the text, click the link button, and type or paste the full address (e.g.
`https://www.example.com/page`). Click the link button on linked text again to change or remove it.

**Images.** There is no upload button. An image can get into the article in two ways:

- **paste** copied image content into the text area (it is stored inside the article as a data URL);
- in **HTML source** mode, insert an `<img src="https://…" alt="…">` tag that points to an image
  already hosted on the web.

Pasted images count towards the size limit of the language version (see
[section 12](#12-limits-and-error-messages)), so prefer small or compressed images, or link to hosted
ones.

**HTML source (`<>`).** This shows the article's raw HTML for fine adjustments: fixing a messy paste,
adding `alt` text to an image, removing stray formatting. Click `<>` again to return to the
formatted view.

> **Security note:** what you store is exactly what the editor produced, but every reader's browser
> **sanitizes** the HTML before showing it (NiceGUI's `ui.html`, using DOMPurify). Scripts, event
> handlers (`onclick` …) and similar active content are stripped. Anything that relies on them won't
> work for readers.

**Pasting from Word or web pages** often brings hidden styles along. After pasting, select the text
and use **remove formatting**, or check the HTML source.

## 7. Who can read the article (visibility)

The **Kdo článek uvidí** (*Who can see the article*) box offers three options:

| Option | Who can read it | Appears in **Články** list |
|---|---|---|
| **Jen já (koncept)** (*Only me (draft)*) | Only you | No (only in **Moje články**) |
| **Vybraní uživatelé** (*Selected users*) | You and the listed email addresses, after logging in | Yes, for those readers, with the badge **Sdíleno s vámi** (*Shared with you*) |
| **Všichni** (*Everyone*) | Everyone, including visitors who are not logged in | Yes |

**Selected users.** When you choose this option, a field **E-maily čtenářů** (*Readers' emails*)
appears:

- separate addresses with commas, semicolons, spaces or new lines;
- letter case and surrounding spaces don't matter, and duplicates are removed;
- you may list people who **don't have an account yet**. They see the article once they log in with
  that address;
- at least one address is required, and at most 200;
- readers never see who else the article is shared with. Only you see the list.

The list is kept when you switch to another visibility. If you go back to **Vybraní uživatelé**
later, the addresses are still there.

For anyone without access, a restricted or draft article looks exactly like a nonexistent one: **Článek
neexistuje, nebo k němu nemáte přístup.** (*The article doesn't exist, or you don't have access to
it.*).

## 8. Saving and publishing

There is one main button, and its label depends on the visibility:

- **Uložit koncept** (*Save draft*) when visibility is **Jen já**. Confirmation: **Uloženo**
  (*Saved*).
- **Publikovat** (*Publish*) for **Vybraní uživatelé** or **Všichni**. Confirmation:
  **Publikováno** (*Published*).

Good to know:

- **There is no autosave.** Leaving or reloading the page discards unsaved changes, so save often.
  Saving a draft is harmless.
- **Publication date.** The date shown to readers is the date the article was **first** published.
  If you switch it back to a draft and publish it again later, the original date is kept. Before the
  first publication, readers would see the last-edit date, but drafts aren't visible to them anyway.
- **Unpublishing.** Switch visibility to **Jen já (koncept)** and save. The article disappears for
  readers immediately.
- If a save fails, a red message appears above the buttons (see
  [section 12](#12-limits-and-error-messages)). Your text stays in the editor, so fix the problem and
  save again.

## 9. Editing an existing article

Open the editor in one of these ways:

- click the article in **Moje články**; or
- open the article in the reader view (**Články**) and click **Upravit** (*Edit*) next to the byline.
  Only you see that link, together with a visibility badge.

In the editor, **Zobrazit** (*View*) opens the reader view of the **last saved** state. Save first if
you want to see your latest changes.

Every save replaces the whole article with what the editor holds: both language versions, the
visibility and the readers list.

## 10. Deleting an article

1. Open the article in the editor.
2. Click **Smazat** (*Delete*) at the bottom right.
3. Confirm in the dialog **Opravdu smazat článek „…“?** (*Really delete the article "…"?*).

Deletion is **permanent**. All language versions and the readers list are removed, and there is no
recycle bin. If you only want to hide the article, unpublish it instead (see
[section 8](#8-saving-and-publishing)).

## 11. What readers see

- **Language.** Readers get the version in their UI language. They switch the language with the
  **English** / **Čeština** button in the top bar of the portal, or in the account menu on the main
  page. The choice is remembered in their browser.
- **Missing version.** If the article doesn't exist in the reader's language, they get the other
  version:
  - in the **Články** list, the article carries a badge **Jen anglicky** / **Jen česky** (*English
    only* / *Czech only*);
  - on the article page, a notice is shown above the text, e.g. **Tento článek je zatím dostupný jen
    v angličtině.** (*This article is only available in English so far.*).
- **Both versions.** The article page offers a link to the other language, **Read in English** /
  **Číst česky**. Clicking it switches the reader's UI language.
- **Byline.** Your author name and the publication date, e.g. *Jana Nová · 09. 10. 2026*.

## 12. Limits and error messages

| Limit | Value |
|---|---|
| Title length | 200 characters per language version |
| Body size | about 2 MB of HTML per language version (pasted images count) |
| Readers of a restricted article | 200 email addresses |
| Author byline | 120 characters |

| Message (Czech) | English | What to do |
|---|---|---|
| Vyplňte prosím nadpis a text aspoň jedné jazykové verze. | Please fill in the title and text of at least one language version. | Fill in at least one tab |
| Doplňte prosím nadpis (verze: …). | Please add a title (version: …). | The named tab has text but no title. Add a title, or clear the text to drop that version |
| Nadpis je příliš dlouhý (nejvýše 200 znaků). | The title is too long (at most 200 characters). | Shorten the title |
| Článek je příliš dlouhý - zkuste zmenšit nebo odebrat vložené obrázky. | The article is too long - try shrinking or removing embedded images. | Remove or shrink pasted images, or use hosted images instead |
| Neplatná e-mailová adresa: … | Invalid email address: … | Fix the address shown |
| Zadejte aspoň jeden e-mail čtenáře, nebo zvolte jinou viditelnost. | Enter at least one reader's email, or pick a different visibility. | Add a reader or change visibility |
| Příliš mnoho čtenářů (nejvýše 200). | Too many readers (at most 200). | Shorten the list, or publish to everyone |
| Na tuto akci nemáte oprávnění. | You aren't allowed to do this. | Your author role was probably revoked, or you were logged out. Log in again |
| Článek neexistuje. | The article doesn't exist. | It was deleted, or isn't yours |
| Něco se nepovedlo. Zkuste to prosím znovu. | Something went wrong. Please try again. | An unexpected server error. Retry. If it keeps happening, tell the administrator (it is logged on the server; one known cause is a database that hasn't been migrated, see below) |

> **For administrators:** if the articles pages show only **Něco se nepovedlo** right after an
> update, the database schema is probably behind. Run `alembic upgrade head` in `backend/`, or start
> the app with `scripts/run.bat`, which does it automatically (`scripts/fast-run.bat` doesn't).

## 13. Tips and known limitations

- **Save regularly.** There is no autosave and no version history. Once you save, the previous text
  is gone.
- **One editor at a time.** If the same article is open in two tabs, the last save wins and
  overwrites the other tab's changes.
- **Translations are independent.** Changing one language version never updates the other. Keep them
  in sync yourself.
- **Titles in lists** follow the reader's language. A good title in each version matters as much as
  the body.
- **Keep formatting simple.** Headings, paragraphs, lists, quotes and links render consistently.
  Custom HTML styling from the source view may not match the site's design and may be stripped when
  it is sanitized.
- **Test what readers see.** Use **Zobrazit** (*View*) after saving. To check the other language,
  switch the UI language in the top bar.
