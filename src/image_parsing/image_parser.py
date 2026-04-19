import cv2
import os
import numpy as np

def _show(title: str, img: np.ndarray, wait: int = 0):
    cv2.imshow(title, img)
    cv2.waitKey(wait)
    cv2.destroyAllWindows()


def _filter_text_recognition(img, block_size, C):
    img_map = img.copy()

    # Crease / shade masking
    hsv_map = cv2.cvtColor(img_map, cv2.COLOR_BGR2HSV)
    hue, sat, val = cv2.split(hsv_map)
    _, mask_sat = cv2.threshold(sat, 25, 255, cv2.THRESH_BINARY_INV)
    _, mask_val = cv2.threshold(val, 100, 255, cv2.THRESH_BINARY_INV)
    shade_mask = cv2.bitwise_or(mask_sat, mask_val)

    # Img processing
    img_map = cv2.cvtColor(img_map, cv2.COLOR_BGR2GRAY)
    thresh_map = img_map.copy()

    # Removing additional noise
    if min(thresh_map.shape) >= 300:
        thresh_map = cv2.GaussianBlur(thresh_map, (3,3), 0)

    # Threshold map
    thresh_map = cv2.adaptiveThreshold(
        thresh_map, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        C
    )
    # Removing noise in threshold map
    if min(thresh_map.shape) >= 300:
        kernel = np.array([
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ], dtype="uint8"
        )
        thresh_map = cv2.morphologyEx(thresh_map, cv2.MORPH_CLOSE, kernel)

    # Applying shade map
    thresh_map[shade_mask==0] = 0
    
    # Final noise reduction
    img_blur = cv2.GaussianBlur(img_map, (5,5), 0)
    _, ret_map = cv2.threshold(img_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    img_map = cv2.bitwise_and(thresh_map, thresh_map, mask=ret_map)

    return img_map


def _filter_threshold_map(img, block_size, C):
    color_map = img.copy()
    img_map = cv2.cvtColor(color_map, cv2.COLOR_BGR2GRAY)
    img_map = cv2.adaptiveThreshold(
        img_map, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        C,
    )    
    return cv2.bitwise_and(img_map, img_map)


def load_and_threshold(path: str, size: int = 450, debug: bool = False):
    block_size = 27
    c = 3
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read: {path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if debug:
        _show("Grayscale", gray)
    
    thresh = _filter_threshold_map(img, block_size, c)
    if debug:
        _show("Threshold (white=edges/lines)", thresh)

    text_recog = _filter_text_recognition(img, block_size, c)
    if debug:
        _show("Text Recog", text_recog)
    return img, thresh, text_recog


def find_grid_contour(thresh, img, debug: bool = False):
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found")
    if debug:
        all_contours_img = img.copy()
        cv2.drawContours(all_contours_img, contours, -1, (0, 255, 255), 1)
        _show(f"All external contours ({len(contours)} found)", all_contours_img)

    max_grid_contour = max(contours, key=cv2.contourArea)
    max_grid_area = cv2.contourArea(max_grid_contour)

    _, (w, h), _ = cv2.minAreaRect(max_grid_contour)
    if max_grid_area * 1.3 < (w * h):
        max_grid_contour = find_best_rectangle(max_grid_contour)

    if debug:
        grid_img = img.copy()
        cv2.drawContours(grid_img, [max_grid_contour], -1, (0, 255, 0), 3)
        area = cv2.contourArea(max_grid_contour)
        _show(f"Largest contour = grid (area={area:.0f} pixels)", grid_img)

    return max_grid_contour


def filter_numbers_and_noise(thresh, grid_contour, mask):
    grid_area = cv2.contourArea(grid_contour)
    expected_cell_area = grid_area / 81
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        cell_area = cv2.contourArea(c)
        if cell_area < expected_cell_area // 3:
            cv2.drawContours(mask, [c], -1, (0,0,0), -1)
    masked = cv2.bitwise_and(thresh, mask)
    return masked


def fix_vertical_and_horizontal_lines(mask):
    h, w = mask.shape
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, w//85))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, vertical_kernel)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h//85, 1))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, horizontal_kernel)
    return mask


def find_cells(thresh, grid_contour, img, debug: bool = False):
    mask = np.zeros_like(thresh)
    cv2.drawContours(mask, [grid_contour], -1, 255, -1)
    if debug:
        _show("Grid mask", mask)

    masked = filter_numbers_and_noise(thresh, grid_contour, mask)
    if debug:
        _show("Thresh masked to grid area", masked)

    masked = fix_vertical_and_horizontal_lines(masked)
    if debug:
        _show("Adjusted vertical and horizontal lines", thresh)

    contours, _ = cv2.findContours(masked, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    grid_area = cv2.contourArea(grid_contour)
    expected = grid_area / 81
    lo, hi = 0.5 * expected, 1.5 * expected
    if debug:
        print(f"Grid area: {grid_area:.0f} | Expected cell: {expected:.0f} | Range: {lo:.0f}–{hi:.0f}")

    rejected_area, rejected_shape, candidates = [], [], []
    for c in contours:
        area = cv2.contourArea(c)
        if not (lo < area < hi):
            rejected_area.append(c)
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.1 * peri, True)
        if len(approx) == 4:
            candidates.append(approx)
        else:
            rejected_shape.append(c)

    if debug:
        reject_img = img.copy()
        cv2.drawContours(reject_img, rejected_area, -1, (0, 0, 255), 1)
        cv2.drawContours(reject_img, rejected_shape, -1, (255, 0, 255), 1)
        cv2.drawContours(reject_img, candidates, -1, (0, 255, 0), 2)
        _show(
            f"Candidates: green={len(candidates)}  red=wrong-area({len(rejected_area)})  magenta=not-quad({len(rejected_shape)})",
            reject_img,
        )
        print(f"Accepted: {len(candidates)} | Rejected area: {len(rejected_area)} | Rejected shape: {len(rejected_shape)}")

    return candidates


def sort_cells(cells, debug: bool = False):
    def top_left(c):
        pts = c.reshape(4, 2)
        s = pts.sum(axis=1)
        return pts[np.argmin(s)]

    cells_with_pos = [(top_left(c), c) for c in cells]
    cells_with_pos.sort(key=lambda x: x[0][1])
    sorted_cells = []
    for idx in range(9):
        cell_row = cells_with_pos[idx * 9 : (idx + 1) * 9]
        cell_row.sort(key=lambda x: x[0][0])
        sorted_cells.extend([c for _, c in cell_row])
    
    return sorted_cells


def find_best_rectangle(contour: np.ndarray, padding: float = 4.0):
    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
    pts = approx.reshape(-1, 2).astype("float32")
    n = len(pts)
    if n < 4:
        raise ValueError(f"Detected grid has fewer than 4 points ({n} points)")

    if n > 4:
        scores = []
        for i in range(n):
            p_prev = pts[(i - 1) % n]
            p_curr = pts[i]
            p_next = pts[(i + 1) % n]
            v_in  = p_prev - p_curr
            v_out = p_next - p_curr
            len_in  = np.linalg.norm(v_in)
            len_out = np.linalg.norm(v_out)
            if len_in == 0 or len_out == 0:
                scores.append(0.0)
                continue

            cos_angle = np.dot(v_in, v_out) / (len_in * len_out)
            right_angle_score = 1.0 - abs(cos_angle)
            scores.append((len_in + len_out) * right_angle_score)

        top4_idx = sorted(np.argsort(scores)[-4:])
        pts = pts[top4_idx]

    centroid = pts.mean(axis=0)
    expanded = []
    for pt in pts:
        direction = pt - centroid
        norm = np.linalg.norm(direction)
        expanded.append(pt + direction / norm * padding)
    return np.array(expanded, dtype="float32").reshape(4, 1, 2).astype("int32")


def rotate_to_upright(*imgs, grid_contour: np.ndarray):
    _, (w, h), angle = cv2.minAreaRect(grid_contour)
    if 90 - abs(angle) < 10:
        return *imgs, grid_contour
    if w < h:
        angle += 90

    img_h, img_w = imgs[0].shape[:2]
    center = (img_w / 2, img_h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    new_w = int(img_h * sin + img_w * cos)
    new_h = int(img_h * cos + img_w * sin)
    M[0, 2] += (new_w - img_w) / 2
    M[1, 2] += (new_h - img_h) / 2

    rotated_imgs = tuple(cv2.warpAffine(img, M, (new_w, new_h)) for img in imgs)

    # Apply the same matrix to the contour points directly
    pts = grid_contour.reshape(-1, 2).astype("float32")
    rotated_pts = cv2.transform(pts[np.newaxis], M)[0]
    rotated_contour = rotated_pts.reshape(-1, 1, 2).astype("int32")

    return *rotated_imgs, rotated_contour


def warp_grids(*args, contour: np.ndarray, sizes: int|list[int] = 50):
    if isinstance(sizes, list):
        if len(args) != len(sizes):
            sizes = [sizes[0]] * len(args)
    
    if isinstance(sizes, int):
        sizes = [sizes] * len(args)
    
    results = []
    for idx, arg in enumerate(args):
        results.append(warp_grid(arg, contour, sizes[idx]))

    return tuple(results)


def warp_grid(img, contour, size: int = 50) -> np.ndarray:
    pts = contour.reshape(4, 2).astype("float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).ravel()
    src = np.array([
        pts[np.argmin(s)],
        pts[np.argmin(diff)],
        pts[np.argmax(s)],
        pts[np.argmax(diff)],
    ], dtype="float32")
    dst = np.array([[0,0],[size,0],[size,size],[0,size]], dtype="float32")
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (size, size))


def warp_cells(img, contour, size: int = 50, p: int = 4) -> np.ndarray:
    cell = warp_grid(img, contour, size)
    cell[:p, :] = 0   
    cell[-p:, :] = 0  
    cell[:, :p] = 0   
    cell[:, -p:] = 0 
    return cell


def show_cell_grid(cells_warped, label: str = "All cells"):
    _show(label, stack_cells(cells_warped))


def stack_cells(cells):
    rows = []
    for r in range(9):
        row = cells[r*9 : (r + 1)*9]
        if len(row) == 9:
            rows.append(np.hstack(row))
    return np.vstack(rows)


def show_image_on_sudoku_grid(
        cells_warped, 
        label: str = "Sudoku Puzzle",
        cell_size: int = 50,
        line_width: int = 2,
        box_line_width: int = 4,
    ):
    if len(cells_warped) != 81:
        raise ValueError(f"Expected 81 cells, got {len(cells_warped)} instead")
    
    def _offsets():
        # Lines for interbox cells, Box lines for box borders
        pos = [0]
        # Left/Top border
        pos.append(box_line_width)
        for i in range(1, 9):
            gap = box_line_width if i % 3 == 0 else line_width
            pos.append(pos[-1] + cell_size + gap)
        
        # Right/Bottom border
        pos.append(pos[-1] + box_line_width)
        return pos
    
    col_offsets = _offsets()
    row_offsets = _offsets()

    total_w, total_h = col_offsets[-1] + cell_size, row_offsets[-1] + cell_size
    
    canvas = np.zeros((total_h, total_w, 3), dtype="uint8")

    for idx, cell in enumerate(cells_warped):
        row, col = divmod(idx, 9)
        x, y = col_offsets[col + 1], row_offsets[row + 1]
        cell_bgr = cell if cell.ndim == 3 else cv2.cvtColor(cell, cv2.COLOR_GRAY2BGR)
        canvas[y : y + cell_size, x : x + cell_size] = cv2.resize(cell_bgr, (cell_size, cell_size))

    _show(label, canvas)


def show_cells_one_by_one(sorted_cells, image):
    for c in sorted_cells:
        mask = np.zeros_like(image)
        cv2.drawContours(mask, [c], -1, (255, 255, 255), -1)
        result = cv2.bitwise_and(image, mask)
        result[mask==0] = 255
        cv2.imshow("9.1. Final cells", result)
        cv2.waitKey(175)
    cv2.destroyAllWindows()


def parse_sudoku_image(path: str, debug: bool = False) -> tuple[list[np.ndarray], list[np.ndarray]]:
    cell_size = int(os.getenv("sudoku_cell_size".upper(), 50))
    img, thresh, text_recog = load_and_threshold(path, debug=debug)
    grid_contour = find_grid_contour(thresh, img, debug=debug)

    img, thresh, text_recog, grid_contour = rotate_to_upright(img, thresh, text_recog, grid_contour=grid_contour)
    if debug:
        _show("Rotated to upright", img)
    
    cells = find_cells(thresh, grid_contour, img, debug=debug)

    if len(cells) != 81:
        raise ValueError(f"Expected 81 cells, found {len(cells)} — run with debug=True to inspect")


    sorted_cells = sort_cells(cells, debug=debug)

    if debug:
        from src.models.digit_recognition import extract_grid
        extract_grid([text_recog])


    processed_grid = [warp_cells(text_recog, c, cell_size) for c in sorted_cells]
    warped_display_image = [warp_grid(img, c, cell_size) for c in sorted_cells]

    if debug:
        show_cell_grid(warped_display_image, "Final cells (check digits upright + centered)")
    
    if debug:
        show_image_on_sudoku_grid(warped_display_image, "SUDOKU!")

    return processed_grid, warped_display_image


def main():
    import sys
    import os
    from src.models.digit_recognition import generate_puzzle_from_cells, draw_digit_boxes, _READER
    from src.algorithms.uniqueness_solver.complete_solver import solve, display_grid, timeit
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/gallery/SudokuTest_1.png"
    debug = (os.getenv("DEBUG") == "true")
    reader = _READER
    parsed_cells, parsed_image = parse_sudoku_image(path, debug=debug)
    if debug:
        show_cell_grid(parsed_cells, "Cells to be sent for OCR")
        ocr = draw_digit_boxes(grid_img=stack_cells(parsed_image), cells=parsed_cells, debug=debug)
        _show("OCR Values", ocr)
    puzzle = generate_puzzle_from_cells(parsed_cells, reader=reader, debug=debug) #type: ignore
    (solution, givens, status), elapsed_time = timeit(solve)(puzzle, 1) #type: ignore
    display_grid(solution, givens, status, elapsed_time)

if __name__=="__main__":
    main()